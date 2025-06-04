import os
import torch
import torch.distributed as dist
from torch.distributed._tensor import DeviceMesh, Shard, distribute_tensor

def init_distributed():
    dist.init_process_group(backend="nccl", init_method="env://")
    torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))

def shard_simple_tensor():
    rank = dist.get_rank()
    world_size = dist.get_world_size()
    device = torch.device(f"cuda:{rank}")

    mesh = DeviceMesh("cuda", list(range(world_size)))

    # Rank 0 建立 tensor，其它 rank 建 dummy
    if rank == 0:
        full_tensor = torch.tensor([0, 1, 2, 3], dtype=torch.float32, device=device)
        print(f"\n[Rank {rank}] Original full tensor: {full_tensor}")
    else:
        full_tensor = torch.empty(4, dtype=torch.float32, device=device)

    # 廣播給所有人（讓大家都拿到 full tensor）
    # DTensor 的理念是每個 rank 自己初始化/持有自己的 shard，因此沒有內建 API 在 rank 0
    # 上初始化 full tensor，然後把 shard 分給不同的 rank。
    dist.broadcast(full_tensor, src=0)
    print(f"[Rank {rank}] After broadcast, full tensor: {full_tensor}")

    # 每個 rank 抽出自己的 shard
    dtensor = distribute_tensor(full_tensor, mesh, placements=[Shard(0)])
    local_tensor = dtensor.to_local()

    print(f"[Rank {rank}] Local shard: {local_tensor}")

    # 使用 full_tensor() 來查看完整的張量
    complete_tensor = dtensor.full_tensor()
    print(f"[Rank {rank}] DTensor full_tensor: {complete_tensor}")

    # 同步確保輸出順序
    dist.barrier()

if __name__ == "__main__":
    init_distributed()
    shard_simple_tensor()
