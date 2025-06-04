import os
import torch
import torch.distributed as dist
from torch.distributed._tensor import DeviceMesh, Shard, distribute_tensor

def init_distributed():
    dist.init_process_group(backend="nccl", init_method="env://")
    torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))

def shard_and_gather():
    rank = dist.get_rank()
    world_size = dist.get_world_size()
    device = torch.device(f"cuda:{rank}")

    mesh = DeviceMesh("cuda", list(range(world_size)))

    # Step 1: Rank 0 建立 full tensor，其它 rank 建 dummy
    if rank == 0:
        full_tensor = torch.tensor([0, 1, 2, 3], dtype=torch.float32, device=device)
        print(f"\n[Rank {rank}] Original full tensor: {full_tensor}")
    else:
        full_tensor = torch.empty(4, dtype=torch.float32, device=device)

    # Step 2: 廣播 full tensor 給所有 rank
    dist.broadcast(full_tensor, src=0)

    # Step 3: 建 DTensor + 抽出 local shard
    dtensor = distribute_tensor(full_tensor, mesh, placements=[Shard(0)])
    local_shard = dtensor.to_local()
    print(f"[Rank {rank}] Local shard: {local_shard}")

    # Step 4: 將 local shard 傳送給 rank 0
    if rank == 0:
        gathered = [torch.empty_like(local_shard) for _ in range(world_size)]
        gathered[0].copy_(local_shard)
        for src in range(1, world_size):
            dist.recv(gathered[src], src=src)
            print(f"[Rank 0] Received shard from rank {src}, shard: {gathered[src]}")
        final_tensor = torch.cat(gathered, dim=0)
        print(f"[Rank 0] Gathered full tensor: {final_tensor}")
    else:
        print(f"[Rank {rank}] Sending local shard to rank 0 by dist.send()")
        dist.send(local_shard, dst=0)

    dist.barrier()

if __name__ == "__main__":
    init_distributed()
    shard_and_gather()
