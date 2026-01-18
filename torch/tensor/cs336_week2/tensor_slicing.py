import torch

def same_storage(x: torch.Tensor, y: torch.Tensor):
    return x.untyped_storage().data_ptr() == y.untyped_storage().data_ptr()

x = torch.tensor([[1., 2, 3], [4, 5, 6]])  # @inspect x
# Many operations simply provide a different view of the tensor.
# This does not make a copy, and therefore mutations in one tensor affects the other.
# Get row 0:
y = x[0]  # @inspect y
assert torch.equal(y, torch.tensor([1., 2, 3]))
assert same_storage(x, y)
# Get column 1:
y = x[:, 1]  # @inspect y
assert torch.equal(y, torch.tensor([2, 5]))
assert same_storage(x, y)
# View 2x3 matrix as 3x2 matrix:
y = x.view(3, 2)  # @inspect y
assert torch.equal(y, torch.tensor([[1, 2], [3, 4], [5, 6]]))
assert same_storage(x, y)
# Transpose the matrix:
y = x.transpose(1, 0)  # @inspect y
assert torch.equal(y, torch.tensor([[1, 4], [2, 5], [3, 6]]))
assert same_storage(x, y)
# Check that mutating x also mutates y.
x[0][0] = 100  # @inspect x, @inspect y
assert y[0][0] == 100
# Note that some views are non-contiguous entries, which means that further views aren't possible.
x = torch.tensor([[1., 2, 3], [4, 5, 6]])  # @inspect x
y = x.transpose(1, 0)  # @inspect y
assert not y.is_contiguous()
try:
    y.view(2, 3)
    assert False
except RuntimeError as e:
    assert "view size is not compatible with input tensor's size and stride" in str(e)
# One can enforce a tensor to be contiguous first:
y = x.transpose(1, 0).contiguous().view(2, 3)  # @inspect y
assert not same_storage(x, y)
# Views are free, copying take both (additional) memory and compute.