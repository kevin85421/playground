# FSDP `state_dict()`

```sh
torchrun --nproc_per_node=4 fsdp_state_dict.py
```

* `FSDP(model)`: 將模型的 Parameter 按照 dim=0（通常是 row-wise） 切分成多份
* `FULL_STATE_DICT`: 每個 rank 都有完整的 state_dict
* `SHARDED_STATE_DICT`: 每個 rank 只有自己的 shard

# FSDP `FULL_STATE_DICT`

```sh
torchrun --nproc_per_node=4 fsdp_state_dict_hang.py
```

* 需要每個 rank 都執行 `state_dict()`，不然會卡住。
* 此例子中，只有 rank 0 執行 `state_dict()`，因此卡住。