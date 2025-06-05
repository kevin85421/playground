# DTensor `distribute_tensor` + `full_tensor()` ([full_tensor_example.py](./full_tensor_example.py))

* 需要四個 GPU

```sh
torchrun --nproc_per_node=4 full_tensor_example.py

# W0604 08:55:09.861638 18197 site-packages/torch/distributed/run.py:792]
# W0604 08:55:09.861638 18197 site-packages/torch/distributed/run.py:792] *****************************************
# W0604 08:55:09.861638 18197 site-packages/torch/distributed/run.py:792] Setting OMP_NUM_THREADS environment variable for each process to be 1 in default, to avoid your system being overloaded, please further tune the variable for optimal performance in your application as needed.
# W0604 08:55:09.861638 18197 site-packages/torch/distributed/run.py:792] *****************************************

# [Rank 0] Original full tensor: tensor([0., 1., 2., 3.], device='cuda:0')
# [Rank 0] After broadcast, full tensor: tensor([0., 1., 2., 3.], device='cuda:0')
# [Rank 1] After broadcast, full tensor: tensor([0., 1., 2., 3.], device='cuda:1')
# [Rank 2] After broadcast, full tensor: tensor([0., 1., 2., 3.], device='cuda:2')
# [Rank 3] After broadcast, full tensor: tensor([0., 1., 2., 3.], device='cuda:3')
# [Rank 0] Local shard: tensor([0.], device='cuda:0')
# [Rank 1] Local shard: tensor([1.], device='cuda:1')
# [Rank 2] Local shard: tensor([2.], device='cuda:2')
# [Rank 3] Local shard: tensor([3.], device='cuda:3')
# [Rank 0] DTensor full_tensor: tensor([0., 1., 2., 3.], device='cuda:0')
# [Rank 1] DTensor full_tensor: tensor([0., 1., 2., 3.], device='cuda:1')
# [Rank 2] DTensor full_tensor: tensor([0., 1., 2., 3.], device='cuda:2')
# [Rank 3] DTensor full_tensor: tensor([0., 1., 2., 3.], device='cuda:3')
# [rank0]:[W604 08:55:15.856186408 ProcessGroupNCCL.cpp:1496] Warning: WARNING: destroy_process_group() was not called before program exit, which can leak resources. For more info, please see https://pytorch.org/docs/stable/distributed.html#shutdown (function operator())
```

# [gather_shards_and_concat.py](./gather_shards_and_concat.py)

* 使用 NCCL 傳送 local shard 給 rank 0，並且在 rank 0 上 concat 所有 shard 成為 full tensor


```sh
torchrun --nproc_per_node=4 gather_shards_and_concat.py

# W0604 09:06:17.409818 24924 site-packages/torch/distributed/run.py:792]
# W0604 09:06:17.409818 24924 site-packages/torch/distributed/run.py:792] *****************************************
# W0604 09:06:17.409818 24924 site-packages/torch/distributed/run.py:792] Setting OMP_NUM_THREADS environment variable for each process to be 1 in default, to avoid your system being overloaded, please further tune the variable for optimal performance in your application as needed.
# W0604 09:06:17.409818 24924 site-packages/torch/distributed/run.py:792] *****************************************

# [Rank 0] Original full tensor: tensor([0., 1., 2., 3.], device='cuda:0')
# [Rank 0] Local shard: tensor([0.], device='cuda:0')
# [Rank 1] Local shard: tensor([1.], device='cuda:1')
# [Rank 1] Sending local shard to rank 0 by dist.send()
# [Rank 2] Local shard: tensor([2.], device='cuda:2')
# [Rank 2] Sending local shard to rank 0 by dist.send()
# [Rank 3] Local shard: tensor([3.], device='cuda:3')
# [Rank 3] Sending local shard to rank 0 by dist.send()
# [Rank 0] Received shard from rank 1, shard: tensor([1.], device='cuda:0')
# [Rank 0] Received shard from rank 2, shard: tensor([2.], device='cuda:0')
# [Rank 0] Received shard from rank 3, shard: tensor([3.], device='cuda:0')
# [Rank 0] Gathered full tensor: tensor([0., 1., 2., 3.], device='cuda:0')
# [rank0]:[W604 09:06:22.151448063 ProcessGroupNCCL.cpp:1496] Warning: WARNING: destroy_process_group() was not called before program exit, which can leak resources. For more info, please see https://pytorch.org/docs/stable/distributed.html#shutdown (function operator())
```

# `dtensor.to(device=...)` [dtensor_to.py](./dtensor_to.py)

* `dtensor.to(device=device)`
  * 並不會把整個 dtensor 傳送到 device，而是把 dtensor 的 local shard 傳送到 device。
  * `device` 跟 `dtensor.DeviceMesh` 不相關，`device` (`torch.cuda.current_device()`) 為 local device，例如：
    * 在一個 process 中 `CUDA_VISIBLE_DEVICES=0`，`device=0` 為 `cuda:0`
    * 在一個 process 中 `CUDA_VISIBLE_DEVICES=1`，`device=0` 為 `cuda:1`

* 此例子中有 4 個 process，每個 process 有 1 個 GPU，每個 process 有一個 dtensor shard，接著呼叫 `dtensor.to(device=device)` 會把 local shard 傳送到 `device` 上，並且在 `device` 上建立一個新的 dtensor shard。

```sh
torchrun --nproc_per_node=4 dtensor_to.py
# W0605 09:02:44.681390 294727 site-packages/torch/distributed/run.py:792]
# W0605 09:02:44.681390 294727 site-packages/torch/distributed/run.py:792] *****************************************
# W0605 09:02:44.681390 294727 site-packages/torch/distributed/run.py:792] Setting OMP_NUM_THREADS environment variable for each process to be 1 in default, to avoid your system being overloaded, please further tune the variable for optimal performance in your application as needed.
# W0605 09:02:44.681390 294727 site-packages/torch/distributed/run.py:792] *****************************************
# [Rank 0] Original tensor: tensor([0., 1., 2., 3.], device='cuda:0')
# [Rank 0] Local shard: tensor([0.], device='cuda:0')
# [Rank 0] full_tensor: tensor([0., 1., 2., 3.], device='cuda:0')
# [Rank 1] Local shard: tensor([1.], device='cuda:1')
# [Rank 1] full_tensor: tensor([0., 1., 2., 3.], device='cuda:1')
# [Rank 2] Local shard: tensor([2.], device='cuda:2')
# [Rank 2] full_tensor: tensor([0., 1., 2., 3.], device='cuda:2')
# [Rank 3] Local shard: tensor([3.], device='cuda:3')
# [Rank 3] full_tensor: tensor([0., 1., 2., 3.], device='cuda:3')
# [rank0]:[W605 09:02:50.822133667 ProcessGroupNCCL.cpp:1496] Warning: WARNING: destroy_process_group() was not called before program exit, which can leak resources. For more info, please see https://pytorch.org/docs/stable/distributed.html#shutdown (function operator())
```