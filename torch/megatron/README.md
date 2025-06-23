# Megatron-LM

## 使用 torch 實現 Megatron-LM TP

* 實現 Fig. 3(a) MLP 和 Fig. 3(b) Attention 的 TP 實現
* Paper: https://arxiv.org/pdf/1909.08053

```
torchrun --nproc_per_node=2 megatron_tp_torch.py
```