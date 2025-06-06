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
    # 將模型的 Parameter 按照 dim=0（通常是 row-wise） 切分成多份
    fsdp_model = FSDP(model)

    # 取得 full state_dict（所有 rank 都會有完整參數）
    with FSDP.state_dict_type(fsdp_model, StateDictType.FULL_STATE_DICT, FullStateDictConfig(offload_to_cpu=True, rank0_only=False)):
        full_state = fsdp_model.state_dict()
        print(f"[Rank {rank}] full_state_dict keys: {list(full_state.keys())}, param: {full_state['linear.weight']} ...")

    # 每個 rank 只有自己的 shard
    with FSDP.state_dict_type(fsdp_model, StateDictType.SHARDED_STATE_DICT, ShardedStateDictConfig(offload_to_cpu=True)):
        sharded_state = fsdp_model.state_dict()
        print(f"[Rank {rank}] sharded_state_dict keys: {list(sharded_state.keys())}")
        lw = sharded_state['linear.weight']
        for i, shard in enumerate(lw.local_shards()):
            print(f"[Rank {rank}] local_shard {i}: {shard.tensor}")

    dist.barrier()

if __name__ == "__main__":
    init_distributed()
    main()
