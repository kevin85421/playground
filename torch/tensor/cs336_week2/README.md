# Stanford CS336 Week 2

* https://stanford-cs336.github.io/spring2025-lectures/?trace=var/traces/lecture_02.json

# Memory accounting

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

# Compute accounting

## Tensor on GPUs

* 把 tensor 傳送到 GPU 上
    ```python
    >>> import torch
    >>> x = torch.zeros(32, 32)
    >>> x.device
    device(type='cpu')
    >>> memory_allocated = torch.cuda.memory_allocated()
    >>> memory_allocated
    0
    >>> y = x.to("cuda:0")
    >>> y.device
    device(type='cuda', index=0)
    >>> z = torch.zeros(32, 32, device="cuda:0")
    >>> new_memory_allocated = torch.cuda.memory_allocated()
    >>> new_memory_allocated - memory_allocated
    8192
    >>> y.numel() * y.element_size() + z.numel() * z.element_size()
    8192
    ```
    * tensor 預設在 CPU 上，使用 `x.to("cuda:0")` 把 tensor 傳送到 GPU 上。

## Tensor operations

* Tensor storage (`tensor.stride()` example)
    ```sh
    python3 tensor_storage.py
    # row 1, col 2, index 6, value 6, stride (4, 1)
    ```
    * PyTorch tensors are `pointers` into allocated memory with metadata (例如：`stride`) describing how to get to any element of the tensor.
    * 對於多維 tensor，底層仍是連續記憶體，Example：
        ```python
        x = torch.tensor([
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [8, 9, 10, 11],
            [12, 13, 14, 15],
            [16, 17, 18, 19],
            [20, 21, 22, 23],
            [24, 25, 26, 27],
            [28, 29, 30, 31],
        ])
        ```
        * 如果要跳轉到下一個 row 需要移動 `stride(0)` (4) 個元素，如果要跳轉到下一個 column 需要移動 `stride(1)` (1) 個元素。
        * 因此假設如果要存取 `x[1][2]`，需要移動 `1 * stride(0) + 2 * stride(1)` 個元素。

* Tensor slicing (`view()`)
    ```sh
    python3 tensor_slicing.py
    ```
    * 很多 operations 只是提供對於 tensor 的不同 "view"，不會真的去 copy，因此對於一個 tensor 的 mutation 會影響到另一個 tensor。
      * Example 1:
        ```python
        x = torch.tensor([[1., 2, 3], [4, 5, 6]])
        y = x[0]
        assert torch.equal(y, torch.tensor([1., 2, 3]))
        assert x.untyped_storage().data_ptr() == y.untyped_storage().data_ptr()
        ```
      * Example 2:
        ```python
        # 記憶體為：[1., 2, 3, 4, 5, 6]
        x = torch.tensor([[1., 2, 3], [4, 5, 6]])
        y = x.transpose(1, 0)
        assert torch.equal(y, torch.tensor([[1, 4], [2, 5], [3, 6]]))
        assert x.untyped_storage().data_ptr() == y.untyped_storage().data_ptr()
        ```
    * 注意：有些 view 是 non-contiguous (底層記憶體不連續)，表示無法再進行進一步的 view。
      * Example:
        ```python
        x = torch.tensor([[1., 2, 3], [4, 5, 6]])  # @inspect x
        y = x.transpose(1, 0)
        assert not y.is_contiguous()
        y.view(2, 3) # => 報錯
        ```
      * 解決方法：使用 `contiguous()` 把 tensor 變成連續的。
        ```python
        y = x.transpose(1, 0).contiguous().view(2, 3)  # @inspect y
        assert x.untyped_storage().data_ptr() != y.untyped_storage().data_ptr()
        ```

* Tensor elementwise
    ```python
    >>> import torch
    >>> x = torch.tensor([1, 4, 9])
    >>> x
    tensor([1, 4, 9])
    >>> x.pow(2)
    tensor([ 1, 16, 81])
    >>> x.sqrt()
    tensor([1., 2., 3.])
    >>> x.rsqrt()
    tensor([1.0000, 0.5000, 0.3333])
    >>> x + x
    tensor([ 2,  8, 18])
    >>> x * 2
    tensor([ 2,  8, 18])
    >>> x / 0.5
    tensor([ 2.,  8., 18.])
    >>> x = torch.ones(3, 3).triu()
    >>> x
    tensor([[1., 1., 1.],
            [0., 1., 1.],
            [0., 0., 1.]])
    ```
    * `triu()` Returns the upper triangular part of a matrix (2-D tensor) or batch of matrices input, the other elements of the result tensor out are set to 0.
      * https://docs.pytorch.org/docs/stable/generated/torch.triu.html

## Einops

* Motivation:
  ```
  >>> x = torch.ones(2, 3, 4)
  >>> x.transpose(1, 2)
  tensor([[[1., 1., 1.],
          [1., 1., 1.],
          [1., 1., 1.],
          [1., 1., 1.]],

          [[1., 1., 1.],
          [1., 1., 1.],
          [1., 1., 1.],
          [1., 1., 1.]]])
  >>> x.transpose(-2, -1)
  tensor([[[1., 1., 1.],
          [1., 1., 1.],
          [1., 1., 1.],
          [1., 1., 1.]],

          [[1., 1., 1.],
          [1., 1., 1.],
          [1., 1., 1.],
          [1., 1., 1.]]])
  ```
  * [torch.transpose](https://docs.pytorch.org/docs/stable/generated/torch.transpose.html)
    * `transpose(dim0, dim1)` 把第 `dim0` 維和第 `dim1` 維交換。 => 複雜 => einops 簡化

* `jaxtyping`
  ```python
  # How do you keep track of tensor dimensions?
  # Old way:
  x = torch.ones(2, 2, 1, 3)  # batch seq heads hidden  @inspect x
  # New (jaxtyping) way:
  x: Float[torch.Tensor, "batch seq heads hidden"] = torch.ones(2, 2, 1, 3)  # @inspect x
  # Note: this is just documentation (no enforcement).
  ```

* `einops_einsum`
  * Example 1: 和 `a @ b` 等價
    ```python
    >>> import torch
    >>> a = torch.tensor([[1,2,3], [4,5,6]])
    >>> b = torch.tensor([[7,8],[9,10],[11,12]])
    >>> torch.einsum("ik,kj->ij", a, b)
    tensor([[ 58,  64],
            [139, 154]])
    ```

* Example 2: 注意 `torch.einsum` 只接受單一 character 作為 dimension，不支持像是 `batch` 這種 multi-character 的 dimension。
  ```python
  >>> import torch
  >>> x = torch.ones(2, 3, 4)
  >>> y = torch.ones(2, 3, 4)
  >>> torch.einsum("bsh,bth->bst", x, y)
  tensor([[[4., 4., 4.],
          [4., 4., 4.],
          [4., 4., 4.]],

          [[4., 4., 4.],
          [4., 4., 4.],
          [4., 4., 4.]]])

  >>> from einops import einsum
  >>> z = einsum(x, y, "batch seq1 hidden, batch seq2 hidden -> batch seq1 seq2")
  >>> z
  tensor([[[4., 4., 4.],
          [4., 4., 4.],
          [4., 4., 4.]],

          [[4., 4., 4.],
          [4., 4., 4.],
          [4., 4., 4.]]])
  ```

* `einops_reduce`
  * Example: 對 `seq` 做 mean
    ```python
    >>> import torch
    >>> from einops import reduce
    >>> x = torch.arange(24).reshape(2, 3, 4)  # batch=2, seq=3, hidden=4
    >>> x
    tensor([[[ 0,  1,  2,  3],
            [ 4,  5,  6,  7],
            [ 8,  9, 10, 11]],

            [[12, 13, 14, 15],
            [16, 17, 18, 19],
            [20, 21, 22, 23]]])
    >>> reduce(x, "batch seq hidden -> batch hidden", "sum")
    tensor([[12, 15, 18, 21],
            [48, 51, 54, 57]])
    ```
    * `"batch seq hidden -> batch hidden"` => 要把 `seq` 壓縮掉，因此把 `batch` / `hidden` 相同的 3 個 elements 加起來。
      * 12 = x[0][0][0] + x[0][1][0] + x[0][2][0] = 0 + 4 + 8 = 12
      * 15 = x[0][0][1] + x[0][1][1] + x[0][2][1] = 1 + 5 + 9 = 15