import torch
import torch.distributed as dist
import os
import time
from datetime import timedelta
import torch.multiprocessing as mp

def worker(rank, world_size):
    print(f"Rank {rank} starting at time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '29501'
    dist.init_process_group("nccl", rank=rank, world_size=world_size, timeout=timedelta(seconds=120))

    device = torch.device(f"cuda:{rank}")
    tensor = torch.tensor([rank], device=device)

    if rank == 0:
        print("Rank 0 waiting to receive...")
        import threading

        def delayed_destroy():
            time.sleep(45)
            print("Rank 0 destroying process group from thread after 45s.")
            dist.destroy_process_group()

        destroy_thread = threading.Thread(target=delayed_destroy, daemon=True)
        destroy_thread.start()
        dist.recv(tensor, src=1)
        destroy_thread.join()
        print("Rank 0 received tensor:", tensor)
    elif rank == 1:
        print("Rank 1 sleeping and skipping send...")
        time.sleep(30)
        print("Rank 1 destroying process group without sending.")
        dist.destroy_process_group()

def run_demo():
    world_size = 2
    mp.spawn(worker, args=(world_size,), nprocs=world_size, join=True)

if __name__ == "__main__":
    run_demo()
