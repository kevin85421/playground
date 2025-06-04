# DTensor `distribute_tensor` + `full_tensor()`

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
