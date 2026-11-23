# Eager vs. 非 eager（`torch.compile` / CUDA graph）

需要 NVIDIA GPU，PyTorch 2.x。

```bash
python eager_vs_graph.py
python eager_vs_graph.py --batch-sizes 1,16,256,4096 --depth 12 --dtype bfloat16
python cuda_graph_pitfalls.py
```

## 為什麼 eager 會慢

eager 模式下，每一行 PyTorch op 都要經過：Python → dispatcher → 選 kernel → `cudaLaunchKernel`。
這段 CPU 時間大約每個 op 5–20 µs。當 GPU 上的 kernel 本身很小（batch 小、dim 小）時，
GPU 大部分時間都在等 CPU 送下一個 kernel —— 這叫 **launch-bound / CPU-bound**。

非 eager 的兩種解法各自處理不同的問題：

| | 解決什麼 | 怎麼做 |
| --- | --- | --- |
| **CUDA graph** | CPU launch overhead | 錄下一整串 kernel，之後一次 `cudaGraphLaunch` 全部送出 |
| **`torch.compile` (default)** | kernel 太多、記憶體來回太多 | Dynamo 抓 graph → Inductor 把 LayerNorm / GELU / residual 等 pointwise op fuse 成少數 Triton kernel |
| **`torch.compile(mode="reduce-overhead")`** | 兩者都有 | Inductor fusion + 自動用 CUDA graph 包起來（cudagraph trees） |

## `eager_vs_graph.py`

一個 8 層 `LayerNorm → Linear → GELU → Linear → scaled residual` 的 MLP，
對不同 batch size 跑四種模式，輸出：

* `first call`：第一次呼叫的時間，也就是 compile / capture 的成本
* `ms/iter`：steady-state 延遲（CUDA event 計時）
* `speedup`：相對於第一個 mode（預設是 eager）
* `launches`：每次 forward CPU 端呼叫幾次 `*LaunchKernel` / `cudaGraphLaunch`（用 `torch.profiler` 數）
* `max |diff|`：和 eager 輸出的最大誤差（bf16 下 1e-2 左右屬正常，因為 fusion 改變了運算順序）

### 實測：A100-SXM4-40GB, torch 2.7.1+cu128, bf16, dim=512, depth=8

```
=== batch size 1 ===
mode                  first call   ms/iter  speedup  launches  max |diff|
eager                      0.00s     0.951    1.00x        65    0.00e+00
cuda_graph                 0.08s     0.188    5.05x         1    0.00e+00
compile                    3.69s     0.582    1.63x        33    3.12e-02
compile+cudagraph          1.58s     0.117    8.12x         2    3.12e-02

=== batch size 16 ===
eager                      0.00s     1.142    1.00x        49    0.00e+00
cuda_graph                 0.15s     0.235    4.86x         1    0.00e+00
compile                    1.98s     0.696    1.64x        49    4.69e-02
compile+cudagraph          1.73s     0.186    6.14x         2    4.69e-02

=== batch size 256 ===
eager                      0.00s     1.171    1.00x        49    0.00e+00
cuda_graph                 0.16s     0.276    4.24x         1    0.00e+00
compile                    1.59s     0.657    1.78x        41    6.25e-02
compile+cudagraph          1.75s     0.222    5.26x         2    6.25e-02

=== batch size 4096 ===
eager                      0.00s     1.424    1.00x        49    0.00e+00
cuda_graph                 0.19s     1.367    1.04x         1    0.00e+00
compile                    1.73s     1.219    1.17x        33    6.25e-02
compile+cudagraph          1.76s     1.207    1.18x         2    6.25e-02
```

觀察：

* **batch 1–256 是 launch-bound**：eager 每次 forward 約 1 ms，幾乎不隨 batch 變化 ——
  時間都花在 CPU 送 49 個 kernel（每層 6 個 × 8 層 + head）。
  只要把 launch 收成 1 次（`cuda_graph`）就快 4–5x；再加上 fusion（`compile+cudagraph`）可到 5–8x。
* **只 fuse 不用 CUDA graph（`compile`）只快 ~1.6x**：kernel 數量減少了，但每次 launch 的 CPU 成本還在。
  batch 16 甚至 launch 數沒變（Inductor 對這個 shape 選了不同的 matmul / epilogue 組合），
  但 Triton kernel 的 launch path 比 eager dispatcher 輕，所以仍然變快。
* **batch 4096 變成 compute-bound**：GPU 時間 > CPU launch 時間，CUDA graph 只快 4%；
  剩下 ~17% 來自 fusion 省下的 memory traffic。
* `first call`：手動 CUDA graph 只要 0.1–0.2 s；`torch.compile` 第一次 3.7 s，
  之後 ~1.6 s 是因為 Inductor 的 on-disk cache（`torch._dynamo.reset()` 不會清它）。
* `max |diff|` 在 bf16 下 3e-2 ~ 6e-2：fusion 改變了累加順序與中間結果的精度，不是 bug。

## `cuda_graph_pitfalls.py`

非 eager 模式換來速度，代價是「動態性」。這個 script 示範四個常見的坑：

1. **output 會被覆蓋**：CUDA graph 的 output 是固定位址，下一次 replay 會寫進同一塊記憶體。
   要保留結果必須 `.clone()`。`reduce-overhead` 也有同樣的語意（存取被覆蓋的 output 會報錯）。
2. **新 input 不會生效**：graph 只認得 capture 時的 input 位址，要 `static_x.copy_(new_x)`。
   `torch.compile(mode="reduce-overhead")` 會自動幫你做這個 copy。
3. **shape 改變**：每個新 shape 都要重新 compile 或重新錄一份 graph。
   用 `TORCH_LOGS=recompiles` 可以看到原因；實務上會把 batch pad 到幾個固定 bucket（vLLM 就是這樣做）。
   A100 上實測（`reduce-overhead`，單層 Linear）：

   ```
   bs=8    1035.17 ms   # compile (static shape) + warmup
   bs=8     211.77 ms   # 錄 CUDA graph
   bs=8       0.32 ms   # replay
   bs=16    169.38 ms   # 新 shape -> 以 dynamic shape 重新 compile
   bs=16    194.11 ms   # 錄 CUDA graph
   bs=32     11.23 ms   # 不用 recompile，但要為這個 shape 錄新的 graph
   bs=8       1.95 ms   # dynamic graph 下 bs=8 也要重錄一次
   bs=33      1.89 ms
   bs=34      1.79 ms
   ```
4. **capture 中不能 CPU sync**：`.item()`、data-dependent control flow 在 manual capture 會直接失敗
   （錯誤訊息是 `operation failed due to a previous error during capture`）；
   `torch.compile` 則是 graph break，切成多段 graph、中間回 eager（實測 `graph_count=2, graph_break_count=1`；
   用 `torch._dynamo.explain` 或 `TORCH_LOGS=graph_breaks` 看）。
   失敗的 capture 會讓 CUDA RNG 卡在 capture 狀態，之後 `nn.Linear(...)` 初始化會報
   `Offset increment outside graph capture`，所以這個 demo 放在最後。

## 什麼時候用哪個

* 先用 `torch.profiler` 看是 launch-bound（GPU timeline 上 kernel 之間有很多空隙）還是 compute-bound。
* 推論、shape 固定或可 bucket 化 → `torch.compile(mode="reduce-overhead")`。
* 不想付 compile 成本、或 model 有 Inductor 不支援的東西 → 手動 `torch.cuda.CUDAGraph`。
* 訓練、shape 常變 → `torch.compile(mode="default")`，必要時 `dynamic=True`。
