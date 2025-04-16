## 使用 NCCL/Gloo 傳輸 `TensorDict`

* https://pytorch.org/tensordict/stable/reference/generated/tensordict.TensorDict.html#tensordict.TensorDict.isend
* 使用 `isend` 和 `irecv` 傳輸 `TensorDict`

```bash
python nccl_send_recv.py

# [Example Output] (使用 GPU devbox)
# [Gloo] Rank 0 is connected to 1 peer ranks. Expected number of connected peer ranks is : 1
# [Gloo] Rank 1 is connected to 1 peer ranks. Expected number of connected peer ranks is : 1
# [client] send  TensorDict(
#     fields={
#         _: Tensor(shape=torch.Size([2, 1, 5]), device=cpu, dtype=torch.float32, is_shared=False),
#         a: TensorDict(
#             fields={
#                 b: Tensor(shape=torch.Size([2]), device=cpu, dtype=torch.float32, is_shared=False)},
#             batch_size=torch.Size([2]),
#             device=None,
#             is_shared=False),
#         c: Tensor(shape=torch.Size([2, 3]), device=cpu, dtype=torch.float32, is_shared=False)},
#     batch_size=torch.Size([2]),
#     device=None,
#     is_shared=False)
# [server] recv  TensorDict(
#     fields={
#         _: Tensor(shape=torch.Size([2, 1, 5]), device=cpu, dtype=torch.float32, is_shared=False),
#         a: TensorDict(
#             fields={
#                 b: Tensor(shape=torch.Size([2]), device=cpu, dtype=torch.float32, is_shared=False)},
#             batch_size=torch.Size([2]),
#             device=None,
#             is_shared=False),
#         c: Tensor(shape=torch.Size([2, 3]), device=cpu, dtype=torch.float32, is_shared=False)},
#     batch_size=torch.Size([2]),
#     device=None,
#     is_shared=False)
```
