import os
import torch
import torch.distributed as dist
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import StateDictType, FullStateDictConfig, ShardedStateDictConfig

def init_distributed():
    dist.init_process_group("nccl", init_method="env://")
    torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))

class ToyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(4, 4)

def main():
    rank = dist.get_rank()
    torch.manual_seed(42)
    model = ToyModel().cuda()
    fsdp_model = FSDP(model)

    # 取得 full state_dict（所有 rank 都會有完整參數）
    with FSDP.state_dict_type(fsdp_model, StateDictType.FULL_STATE_DICT, FullStateDictConfig(offload_to_cpu=True, rank0_only=False)):
        print(f"[Rank {rank}] full_state_dict")
        if rank == 0:
            full_state = fsdp_model.state_dict()
            print(f"[Rank {rank}] full_state_dict keys: {list(full_state.keys())}, param: {full_state['linear.weight']} ...")

    dist.barrier()

if __name__ == "__main__":
    init_distributed()
    main()
