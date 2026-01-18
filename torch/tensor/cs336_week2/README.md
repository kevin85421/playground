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

