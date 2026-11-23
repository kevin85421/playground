"""
比較同一個 model 在四種執行方式下的延遲：

  1. eager                    : 一行 Python 一個（或幾個）kernel launch
  2. cuda_graph (manual)      : 用 torch.cuda.CUDAGraph 錄一次，之後 replay
  3. compile (default)        : torch.compile -> Inductor 產生 fused Triton kernel
  4. compile (reduce-overhead): 3 + 自動把整個 graph 包成 CUDA graph

每種方式都會量：
  * first call  : 第一次呼叫的時間（compile / capture 成本）
  * ms/iter     : steady-state 每次 forward 的時間（CUDA event 計時）
  * launches    : 每次 forward CPU 端送出幾次 launch（kernel launch + graph launch）
  * max |diff|  : 和 eager 輸出的最大誤差

用法：
  python eager_vs_graph.py
  python eager_vs_graph.py --batch-sizes 1,16,256,4096 --depth 12
"""

import argparse
import time

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.profiler import ProfilerActivity, profile


class Block(nn.Module):
    """LayerNorm -> Linear -> GELU -> Linear -> scaled residual。

    除了兩個 matmul 以外都是很小的 pointwise / reduction op，
    eager 下每個 op 都是一個獨立 kernel，正好是 fusion 和 CUDA graph 的目標。
    """

    def __init__(self, dim: int):
        super().__init__()
        self.ln = nn.LayerNorm(dim)
        self.fc1 = nn.Linear(dim, 4 * dim)
        self.fc2 = nn.Linear(4 * dim, dim)
        self.scale = nn.Parameter(torch.full((dim,), 0.5))

    def forward(self, x):
        h = self.ln(x)
        h = F.gelu(self.fc1(h))
        h = self.fc2(h)
        return x + h * self.scale


class Model(nn.Module):
    def __init__(self, dim: int, depth: int):
        super().__init__()
        self.blocks = nn.Sequential(*[Block(dim) for _ in range(depth)])
        self.head = nn.LayerNorm(dim)

    def forward(self, x):
        return self.head(self.blocks(x))


# ---------------------------------------------------------------------------
# 四種執行方式。每個 builder 回傳一個 `fn(x) -> y`。
# ---------------------------------------------------------------------------


def build_eager(model, example):
    return model


def build_cuda_graph(model, example):
    # CUDA graph 錄下的是「固定的 kernel 序列 + 固定的記憶體位址」，
    # 所以 input / output 都必須是 static buffer。
    static_x = example.clone()

    # capture 前要先在 side stream 上 warmup：
    # 讓 cuBLAS workspace、allocator 等 lazy init 不要發生在 capture 裡。
    s = torch.cuda.Stream()
    s.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(s):
        for _ in range(3):
            model(static_x)
    torch.cuda.current_stream().wait_stream(s)

    g = torch.cuda.CUDAGraph()
    with torch.cuda.graph(g):
        static_y = model(static_x)

    def run(x):
        static_x.copy_(x)  # 新資料要「複製進」static buffer，不能換 tensor
        g.replay()
        return static_y  # 注意：下一次 replay 會覆蓋這塊記憶體

    return run


def build_compile_default(model, example):
    return torch.compile(model, mode="default")


def build_compile_reduce_overhead(model, example):
    # reduce-overhead = Inductor fusion + CUDA graphs (cudagraph trees)
    return torch.compile(model, mode="reduce-overhead")


MODES = {
    "eager": build_eager,
    "cuda_graph": build_cuda_graph,
    "compile": build_compile_default,
    "compile+cudagraph": build_compile_reduce_overhead,
}


# ---------------------------------------------------------------------------
# 量測工具
# ---------------------------------------------------------------------------


def time_ms_per_iter(fn, x, iters: int, warmup: int) -> float:
    for _ in range(warmup):
        fn(x)
    torch.cuda.synchronize()

    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(iters):
        fn(x)
    end.record()
    torch.cuda.synchronize()
    return start.elapsed_time(end) / iters


def count_launches_per_iter(fn, x, iters: int = 10) -> float:
    """數 CPU 端 launch API 被呼叫幾次。

    eager / compile 會看到很多 cudaLaunchKernel / cuLaunchKernel（Triton），
    CUDA graph 則只會看到一次 cudaGraphLaunch —— 這就是省下的 overhead。
    """
    torch.cuda.synchronize()
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        for _ in range(iters):
            fn(x)
        torch.cuda.synchronize()

    n = 0
    for evt in prof.key_averages():
        name = evt.key
        if "LaunchKernel" in name or "GraphLaunch" in name:
            n += evt.count
    return n / iters


def run_one(mode: str, model, x, ref, args):
    torch._dynamo.reset()  # 每個 mode 從乾淨的 compile cache 開始

    t0 = time.perf_counter()
    fn = MODES[mode](model, x)
    y = fn(x)
    torch.cuda.synchronize()
    first_call_s = time.perf_counter() - t0

    # clone：CUDA graph 的輸出 buffer 之後會被覆蓋
    max_diff = (y.clone().float() - ref.float()).abs().max().item()
    ms = time_ms_per_iter(fn, x, args.iters, args.warmup)
    launches = count_launches_per_iter(fn, x) if args.profile else float("nan")
    return first_call_s, ms, launches, max_diff


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--batch-sizes", default="1,16,256,4096")
    p.add_argument("--dim", type=int, default=512)
    p.add_argument("--depth", type=int, default=8)
    p.add_argument("--dtype", default="bfloat16", choices=["float32", "bfloat16", "float16"])
    p.add_argument("--iters", type=int, default=200)
    p.add_argument("--warmup", type=int, default=20)
    p.add_argument("--modes", default=",".join(MODES))
    p.add_argument("--no-profile", dest="profile", action="store_false")
    args = p.parse_args()

    assert torch.cuda.is_available(), "這個 example 需要 NVIDIA GPU"
    torch.manual_seed(0)
    dtype = getattr(torch, args.dtype)
    device = "cuda"
    modes = args.modes.split(",")

    print(f"torch {torch.__version__} | {torch.cuda.get_device_name()} | "
          f"dim={args.dim} depth={args.depth} dtype={args.dtype}")

    model = Model(args.dim, args.depth).to(device, dtype).eval()

    with torch.inference_mode():
        for bs in map(int, args.batch_sizes.split(",")):
            x = torch.randn(bs, args.dim, device=device, dtype=dtype)
            ref = model(x).clone()

            print(f"\n=== batch size {bs} ===")
            print(f"{'mode':<20}{'first call':>12}{'ms/iter':>10}{'speedup':>9}"
                  f"{'launches':>10}{'max |diff|':>12}")
            eager_ms = None
            for mode in modes:
                first, ms, launches, diff = run_one(mode, model, x, ref, args)
                eager_ms = eager_ms or ms
                print(f"{mode:<20}{first:>11.2f}s{ms:>10.3f}{eager_ms / ms:>8.2f}x"
                      f"{launches:>10.0f}{diff:>12.2e}")


if __name__ == "__main__":
    main()
