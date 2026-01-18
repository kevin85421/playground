import torch
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
# To go to the next row (dim 0), skip 4 elements in storage.
assert x.stride(0) == 4
# To go to the next column (dim 1), skip 1 element in storage.
assert x.stride(1) == 1
# To find an element:
row, col = 1, 2
index = row * x.stride(0) + col * x.stride(1)  # @inspect index
assert index == 6

# `contiguous()` 把 tensor 變成記憶體中連續
# `view(-1)` 把 tensor 展成 1D 的 tensor
flattened_x = x.contiguous().view(-1)
print(f"row {row}, col {col}, index {index}, value {flattened_x[index]}, stride {x.stride()}")
assert flattened_x[index] == x[row][col]
