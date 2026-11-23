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

預期會看到的趨勢（實際數字依 GPU 而定）：

* **batch 小**：`launches` 從 eager 的上百次 → compile 的幾十次 → CUDA graph 的 **1** 次；
  CUDA graph 和 `compile+cudagraph` 的加速最明顯（常見 3–10x）。
* **batch 大**：時間被 matmul 主導，已經是 compute-bound，CUDA graph 幾乎沒幫助；
  剩下的加速來自 fusion 減少 memory traffic，幅度小很多。
* `first call`：eager / manual CUDA graph 是毫秒級，`torch.compile` 是秒級到數十秒級。

## `cuda_graph_pitfalls.py`

非 eager 模式換來速度，代價是「動態性」。這個 script 示範四個常見的坑：

1. **output 會被覆蓋**：CUDA graph 的 output 是固定位址，下一次 replay 會寫進同一塊記憶體。
   要保留結果必須 `.clone()`。`reduce-overhead` 也有同樣的語意（存取被覆蓋的 output 會報錯）。
2. **新 input 不會生效**：graph 只認得 capture 時的 input 位址，要 `static_x.copy_(new_x)`。
   `torch.compile(mode="reduce-overhead")` 會自動幫你做這個 copy。
3. **shape 改變**：每個新 shape 都要重新 compile 或重新錄一份 graph。
   用 `TORCH_LOGS=recompiles` 可以看到原因；實務上會把 batch pad 到幾個固定 bucket（vLLM 就是這樣做）。
4. **capture 中不能 CPU sync**：`.item()`、data-dependent control flow 在 manual capture 會直接失敗；
   `torch.compile` 則是 graph break，切成多段 graph、中間回 eager（用 `torch._dynamo.explain` 或 `TORCH_LOGS=graph_breaks` 看）。

## 什麼時候用哪個

* 先用 `torch.profiler` 看是 launch-bound（GPU timeline 上 kernel 之間有很多空隙）還是 compute-bound。
* 推論、shape 固定或可 bucket 化 → `torch.compile(mode="reduce-overhead")`。
* 不想付 compile 成本、或 model 有 Inductor 不支援的東西 → 手動 `torch.cuda.CUDAGraph`。
* 訓練、shape 常變 → `torch.compile(mode="default")`，必要時 `dynamic=True`。
