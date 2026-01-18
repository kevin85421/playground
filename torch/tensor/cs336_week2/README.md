# Stanford CS336 Week 2

* https://stanford-cs336.github.io/spring2025-lectures/?trace=var/traces/lecture_02.json


## Tensor memory

* float32 tensor: sign (1 bit) + exponent (8 bits) + fraction (23 bits)
    ```python
    >>> import torch
    >>> x = torch.zeros(4, 8)
    >>> x
    tensor([[0., 0., 0., 0., 0., 0., 0., 0.],
            [0., 0., 0., 0., 0., 0., 0., 0.],
            [0., 0., 0., 0., 0., 0., 0., 0.],
            [0., 0., 0., 0., 0., 0., 0., 0.]])
    >>> x.dtype
    torch.float32
    >>> x.numel()
    32
    >>> x.element_size()
    4
    >>> tensor_memory_bytes = x.numel() * x.element_size()
    >>> tensor_memory_bytes
    128
    ```
    * `x.numel()` 為 tensor 的元素數量，在此例中為 4 * 8 = 32
    * `x.element_size()` 為 tensor 的元素大小，在此例中為 4 bytes
      * 預設的 dtype 為 `torch.float32`，因此元素大小為 4 bytes。
    * `tensor_memory_bytes` 為 tensor 的記憶體大小，在此例中為 32 * 4 = 128 bytes

* float16 tensor: sign (1 bit) + exponent (5 bits) + fraction (10 bits)
    ```python
    >>> import torch
    >>> x = torch.zeros(4, 8, dtype=torch.float16)
    >>> x
    tensor([[0., 0., 0., 0., 0., 0., 0., 0.],
            [0., 0., 0., 0., 0., 0., 0., 0.],
            [0., 0., 0., 0., 0., 0., 0., 0.],
            [0., 0., 0., 0., 0., 0., 0., 0.]], dtype=torch.float16)
    >>> x.element_size()
    2
    >>> x = torch.tensor([1e-8], dtype=torch.float16)
    >>> x
    tensor([0.], dtype=torch.float16)
    ```
    * float16 = fp16 = half precision
    * `x.element_size()` 為 tensor 的元素大小，在此例中為 2 bytes，因為 dtype 為 `torch.float16`。
    * 比較
      * 相比於 float32 使用更少記憶體。
      * 但是在小數字時會 underflow (如上述的 `1e-8`)，會造成 training 時不穩定。

* bfloat16 tensor: sign (1 bit) + exponent (8 bits) + fraction (7 bits)
    ```python
    >>> import torch
    >>> x = torch.tensor([1e-8], dtype=torch.bfloat16)
    >>> x
    tensor([1.0012e-08], dtype=torch.bfloat16)
    >>> torch.finfo(torch.float32)
    finfo(resolution=1e-06, min=-3.40282e+38, max=3.40282e+38, eps=1.19209e-07, smallest_normal=1.17549e-38, tiny=1.17549e-38, dtype=float32)
    >>> torch.finfo(torch.float16)
    finfo(resolution=0.001, min=-65504, max=65504, eps=0.000976562, smallest_normal=6.10352e-05, tiny=6.10352e-05, dtype=float16)
    >>> torch.finfo(torch.bfloat16)
    finfo(resolution=0.01, min=-3.38953e+38, max=3.38953e+38, eps=0.0078125, smallest_normal=1.17549e-38, tiny=1.17549e-38, dtype=bfloat16)
    ```
    * Google Brain 開發 bfloat16 (Brain Floating Point)，使用和 fp16 相同的 memory，但是 dynamic range 和 fp32 相同，犧牲一些 resolution，但是在 deep learning 中可接受。
    * 比較
        * 相比於 fp16，`torch.tensor([1e-8], dtype=torch.bfloat16)` 並沒有造成 underflow。

* fp8
    * https://docs.nvidia.com/deeplearning/transformer-engine/user-guide/examples/fp8_primer.html
    * H100s support two variants of FP8: E4M3 (range [-448, 448]) and E5M2 ([-57344, 57344]).

* Implications on training:
  * 在 training 時，使用 float32 可以正常訓練，但是需要大量記憶體。
  * 使用 fp8、float16 和 bfloat16 訓練時，可能會造成不穩定。
  * 解決方案：使用 `mixed precision training`。
