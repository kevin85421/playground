import os
import torch
import torch.distributed as dist
from torch.distributed._tensor import DeviceMesh, Shard, distribute_tensor

def init_distributed():
    dist.init_process_group(backend="nccl", init_method="env://")
    torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))

def main():
    rank = dist.get_rank()
    world_size = dist.get_world_size()
    local_device = torch.device(f"cuda:{rank}")

    # 建立 DeviceMesh
    mesh = DeviceMesh("cuda", list(range(world_size)))

    # 只在 rank 0 建立完整 tensor，其他 rank 建空 tensor
    if rank == 0:
        full_tensor = torch.tensor([0, 1, 2, 3], dtype=torch.float32, device=local_device)
        print(f"[Rank 0] Original tensor: {full_tensor}")
    else:
        full_tensor = torch.empty(4, dtype=torch.float32, device=local_device)

    # 廣播給所有 rank
    dist.broadcast(full_tensor, src=0)

    # 分 shard
    dtensor = distribute_tensor(full_tensor, mesh, placements=[Shard(0)])

    # 每個 rank 把 dtensor 傳送到自己目前的 GPU（其實已經在正確的 device，但這裡示範 .to() 用法）
    dtensor_on_local = dtensor.to(torch.cuda.current_device())

    # 每個 rank 呼叫 full_tensor()
    full = dtensor_on_local.full_tensor()
    print(f"[Rank {rank}] Local shard: {dtensor_on_local.to_local()}")
    print(f"[Rank {rank}] full_tensor: {full}")

    dist.barrier()

if __name__ == "__main__":
    init_distributed()
    main()
