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
    local_shard = dtensor.to_local()
    print(f"[Rank {rank}] Local shard: {local_shard}")

    gathered = [torch.empty_like(local_shard) for _ in range(world_size)]
    for src in range(world_size):
        if src < rank:
            print(f"[Rank {rank}] Sending shard to rank {src}")
            dist.send(local_shard, dst=src)
        elif src > rank:
            print(f"[Rank {rank}] Receiving shard from rank {src}")
            dist.recv(gathered[src], src=src)
        else:
            gathered[src].copy_(local_shard)

    for src in range(world_size):
        if src > rank:
            print(f"[Rank {rank}] Sending shard to rank {src}")
            dist.send(gathered[src], dst=src)
        elif src < rank:
            print(f"[Rank {rank}] Receiving shard from rank {src}")
            dist.recv(gathered[src], src=src)

    final_tensor = torch.cat(gathered, dim=0)
    print(f"[Rank {rank}] Gathered full tensor: {final_tensor}")

    dist.barrier()

if __name__ == "__main__":
    init_distributed()
    main()
