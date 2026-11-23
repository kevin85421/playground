"""
CUDA graph / torch.compile 非 eager 模式常見的坑，每個 demo 都會印出「看起來不對」的結果。

  1. output 會被下一次 replay 覆蓋
  2. 換一個新的 input tensor 不會生效，必須 copy_ 進 static buffer
  3. shape 改變 -> torch.compile 重新 compile / 重新錄 graph
  4. capture 中不能有 CPU sync（.item()、print tensor ...）

用法：
  python cuda_graph_pitfalls.py
  TORCH_LOGS=recompiles python cuda_graph_pitfalls.py   # 看 recompile 原因
"""

import time

import torch


def capture(fn, static_x):
    s = torch.cuda.Stream()
    s.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(s):
        fn(static_x)
    torch.cuda.current_stream().wait_stream(s)

    g = torch.cuda.CUDAGraph()
    with torch.cuda.graph(g):
        static_y = fn(static_x)
    return g, static_y


def demo_output_aliasing():
    print("\n[1] output 會被下一次 replay 覆蓋")
    static_x = torch.zeros(4, device="cuda")
    g, static_y = capture(lambda x: x * 2, static_x)

    static_x.copy_(torch.full((4,), 1.0, device="cuda"))
    g.replay()
    y1 = static_y  # 沒有 clone

    static_x.copy_(torch.full((4,), 10.0, device="cuda"))
    g.replay()
    y2 = static_y

    print(f"  y1 = {y1.tolist()}  (預期 2.0，但被第二次 replay 改成 20.0)")
    print(f"  y2 = {y2.tolist()}")
    print(f"  y1 is y2: {y1 is y2}  -> 要保留結果請 .clone()")


def demo_new_input_ignored():
    print("\n[2] 換新的 input tensor 不會生效")
    static_x = torch.ones(4, device="cuda")
    g, static_y = capture(lambda x: x + 100, static_x)

    # graph 只認得 static_x 的位址，new_x 根本不會被讀到
    new_x = torch.full((4,), 5.0, device="cuda")
    g.replay()
    print(f"  replay 後 = {static_y.tolist()}  (仍然是 1 + 100，不是 5 + 100)")

    static_x.copy_(new_x)
    g.replay()
    print(f"  copy_ 後  = {static_y.tolist()}")


def demo_cpu_sync_in_capture():
    print("\n[4] capture 中做 CPU sync")

    def fn(x):
        if x.sum().item() > 0:  # .item() 需要等 GPU 算完 -> capture 時不允許
            return x * 2
        return x

    static_x = torch.ones(4, device="cuda")
    g = torch.cuda.CUDAGraph()
    try:
        with torch.cuda.graph(g):
            fn(static_x)
        print("  居然成功了？")
    except Exception as e:  # noqa: BLE001
        # .item() 底下是 cudaMemcpy + sync，capture 中不合法；
        # 錯誤通常以 "operation failed due to a previous error during capture" 浮出來
        print(f"  capture 失敗: {type(e).__name__}: {str(e).splitlines()[0]}")

    # torch.compile 遇到 .item() 不會報錯，而是 graph break：
    # 前後切成兩段 graph，中間回到 eager。可以用 TORCH_LOGS=graph_breaks 看。
    torch._dynamo.reset()
    explanation = torch._dynamo.explain(fn)(static_x)
    print(f"  torch.compile: graph_count={explanation.graph_count}, "
          f"graph_break_count={explanation.graph_break_count}")


def demo_dynamic_shapes():
    print("\n[3] shape 改變 -> recompile / 重新錄 graph")
    torch._dynamo.reset()
    lin = torch.nn.Linear(256, 256, device="cuda")
    fn = torch.compile(lambda x: torch.relu(lin(x)), mode="reduce-overhead")

    # 用 no_grad 而不是 inference_mode：inference tensor 會被 cudagraph trees 留住，
    # 之後的手動 capture 會撞到 "Inplace update to inference tensor" 錯誤
    with torch.no_grad():
        for bs in [8, 8, 8, 16, 16, 32, 8, 33, 34]:
            x = torch.randn(bs, 256, device="cuda")
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            fn(x)
            torch.cuda.synchronize()
            print(f"  bs={bs:<3} {1e3 * (time.perf_counter() - t0):8.2f} ms")
    print("  第一次看到新 shape 會變慢（compile 或 record 新 graph）；")
    print("  第二個不同 shape 之後 dynamo 通常會改成 dynamic shape 再 compile 一次，")
    print("  但 CUDA graph 仍然是每個具體 shape 各錄一份 -> 實務上會把 batch pad 到幾個固定 bucket。")


def main():
    assert torch.cuda.is_available(), "這個 example 需要 NVIDIA GPU"
    demo_output_aliasing()
    demo_new_input_ignored()
    demo_dynamic_shapes()
    # 一定要放最後：capture 失敗後 CUDA RNG 會卡在 capture 狀態，
    # 之後任何 random init 都會報 "Offset increment outside graph capture"
    demo_cpu_sync_in_capture()


if __name__ == "__main__":
    main()
