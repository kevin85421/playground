# Megatron‑style Tensor Parallel Minimal Implementation
# Supports TP MLP and TP Attention inside a Transformer block.

import math
from typing import Optional

import torch
import torch.distributed as dist
from torch import nn
from torch.autograd import Function

# ------------------------
# Distributed setup helpers
# ------------------------
_MODEL_PARALLEL_GROUP: Optional[dist.ProcessGroup] = None

def init_distributed(backend: str = "nccl") -> None:
    """Initialize the default process group. Call after launching with torchrun."""
    if not dist.is_initialized():
        dist.init_process_group(backend=backend)

def initialize_model_parallel(model_parallel_size: int) -> None:
    """Create a tensor‑model‑parallel process group."""
    global _MODEL_PARALLEL_GROUP
    # 總共有 world_size 個 process，每個 TP group 需要 model_parallel_size 個 process。
    # Ex: world_size = 8, model_parallel_size = 2 => TP group 1: GPU 0, 2, 4, 6; TP group 2: GPU 1, 3, 5, 7。
    world_size = dist.get_world_size()
    rank = dist.get_rank()
    assert world_size % model_parallel_size == 0, "world_size must be divisible by mp_size"

    mp_ranks = [r for r in range(world_size) if r % model_parallel_size == rank % model_parallel_size]
    # 使用 `dist.new_group` 建立一個新的 process group。
    _MODEL_PARALLEL_GROUP = dist.new_group(ranks=mp_ranks)

def get_mp_group():
    return _MODEL_PARALLEL_GROUP

def get_mp_rank():
    return dist.get_rank(group=_MODEL_PARALLEL_GROUP)

def get_mp_world_size():
    return dist.get_world_size(group=_MODEL_PARALLEL_GROUP)

# ------------------------
# Megatron-LM style communication functions
# ------------------------
class F(Function):
    """Identity in forward, All‑Reduce in backward (gathers gradients)."""
    @staticmethod
    def forward(ctx, x: torch.Tensor):
        return x

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor):
        dist.all_reduce(grad_output, op=dist.ReduceOp.SUM, group=get_mp_group())
        return grad_output

def f(x: torch.Tensor) -> torch.Tensor:
    return F.apply(x)

class G(Function):
    """All‑Reduce in forward, identity in backward (broadcasts activations)."""
    @staticmethod
    def forward(ctx, x: torch.Tensor):
        dist.all_reduce(x, op=dist.ReduceOp.SUM, group=get_mp_group())
        return x

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor):
        return grad_output

def g(x: torch.Tensor) -> torch.Tensor:
    return G.apply(x)

# ------------------------
# Tensor Parallel Linear layers
# ------------------------
class ColumnParallelLinear(nn.Module):
    """Output‑dim sliced linear layer (Megatron: ColumnParallelLinear)."""
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.mp_world_size = get_mp_world_size()
        assert output_dim % self.mp_world_size == 0, "output_dim must be divisible by mp_world_size"
        output_dim_per_part = output_dim // self.mp_world_size
        self.linear = nn.Linear(input_dim, output_dim_per_part)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.linear(x)
        return out

class RowParallelLinear(nn.Module):
    """Input‑dim sliced linear layer (Megatron: RowParallelLinear)."""
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.mp_world_size = get_mp_world_size()
        assert input_dim % self.mp_world_size == 0, "input_dim must be divisible by mp_world_size"
        input_dim_per_part = input_dim // self.mp_world_size
        self.linear = nn.Linear(input_dim_per_part, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        chunks = torch.chunk(x, self.mp_world_size, dim=-1)
        x_part = chunks[get_mp_rank()]
        out = self.linear(x_part)
        dist.all_reduce(out, group=get_mp_group())
        return out

# ------------------------
# Tensor Parallel MLP
# ------------------------
class TPMLP(nn.Module):
    """Feed‑Forward Network with Tensor Parallel linear layers."""
    def __init__(self, hidden_size: int, ffn_hidden_size: int, activation: type[nn.Module] = nn.GELU, dropout_p: float = 0.0):
        super().__init__()
        # fc1 是 Megatron 論文 Fig. 3(a) 中的 `A`，需要垂直切成 A1, A2。
        self.fc1 = ColumnParallelLinear(hidden_size, ffn_hidden_size)
        self.act = activation()
        # fc2 是 Megatron 論文 Fig. 3(a) 中的 `B`，需要水平切成 B1, B2。
        self.dropout = nn.Dropout(dropout_p)
        self.fc2 = RowParallelLinear(ffn_hidden_size, hidden_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Y = GeLU(XA)
        x = f(x)
        y = self.act(self.fc1(x))
        # Z = Dropout(YB)
        yb = self.fc2(y)
        z = self.dropout(g(yb))
        return z

# ------------------------
# Tensor Parallel Attention
# ------------------------
class TPAttention(nn.Module):
    """Self‑Attention with Tensor Parallel projections following Megatron-LM design."""
    def __init__(self, hidden_size: int, num_attention_heads: int, dropout_p: float = 0.0):
        super().__init__()
        assert hidden_size % num_attention_heads == 0
        self.hidden_size = hidden_size
        self.num_heads = num_attention_heads
        self.head_dim = hidden_size // num_attention_heads
        self.scale = 1.0 / math.sqrt(self.head_dim)
        
        # Get world size for tensor parallelism
        tp_world_size = get_mp_world_size()
        
        # Each rank handles num_heads // world_size heads
        self.num_heads_per_rank = num_attention_heads // tp_world_size
        self.head_dim_per_rank = self.head_dim * self.num_heads_per_rank
        
        # Q, K, V projections: split vertically (by head dimension)
        self.query = ColumnParallelLinear(hidden_size, self.head_dim_per_rank)
        self.key = ColumnParallelLinear(hidden_size, self.head_dim_per_rank)
        self.value = ColumnParallelLinear(hidden_size, self.head_dim_per_rank)
        
        # Output projection: split horizontally (by head dimension)
        self.out_proj = RowParallelLinear(self.head_dim_per_rank, hidden_size)
        
        self.attn_drop = nn.Dropout(dropout_p)
        self.proj_drop = nn.Dropout(dropout_p)

    def _shape(self, x: torch.Tensor, bsz: int, seq_len: int) -> torch.Tensor:
        return x.view(bsz, seq_len, self.num_heads_per_rank, self.head_dim).transpose(1, 2).contiguous()

    def forward(self, x: torch.Tensor, attn_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        bsz, seq_len, _ = x.size()
        
        # Step 1: Apply F() to input (identity in forward, all-reduce in backward)
        x = f(x)
        
        # Step 2: Compute Q, K, V for this rank's subset of heads
        q = self.query(x)  # (batch, seq, head_dim_per_rank)
        k = self.key(x)    # (batch, seq, head_dim_per_rank)
        v = self.value(x)  # (batch, seq, head_dim_per_rank)
        
        # Step 3: Reshape for multi-head attention
        q = self._shape(q, bsz, seq_len)  # (batch, num_heads_per_rank, seq, head_dim)
        k = self._shape(k, bsz, seq_len)
        v = self._shape(v, bsz, seq_len)
        
        # Step 4: Compute attention scores
        attn = (q @ k.transpose(-2, -1)) * self.scale
        
        # Step 5: Apply attention mask
        if attn_mask is not None:
            attn = attn.masked_fill(attn_mask == 0, -1e4)
        
        # Step 6: Apply softmax and dropout
        attention_weights = torch.softmax(attn, dim=-1)
        attention_weights = self.attn_drop(attention_weights)
        
        # Step 7: Apply attention weights to values
        context = attention_weights @ v
        
        # Step 8: Apply G() after attention computation (all-reduce in forward, identity in backward)
        context = g(context)
        
        # Step 9: Reshape back
        context = context.transpose(1, 2).contiguous().view(bsz, seq_len, self.head_dim_per_rank)
        
        # Step 10: Apply output projection
        out = self.out_proj(context)
        out = self.proj_drop(out)
        
        return out

# ------------------------
# Transformer Block with TP
# ------------------------
class TPTransformerBlock(nn.Module):
    def __init__(self, hidden_size: int, num_heads: int, ffn_hidden_size: int, dropout_p: float = 0.1):
        # https://arxiv.org/pdf/1909.08053 (Fig. 2)
        super().__init__()
        self.ln1 = nn.LayerNorm(hidden_size)
        self.attn = TPAttention(hidden_size, num_heads, dropout_p)
        self.ln2 = nn.LayerNorm(hidden_size)
        self.mlp = TPMLP(hidden_size, ffn_hidden_size, dropout_p=dropout_p)

    def forward(self, x: torch.Tensor, attn_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # residual = (本身 x) + (attention 的 output) => 參考宏毅 2021 slide p.19。
        x = x + self.attn(self.ln1(x), attn_mask)
        x = x + self.mlp(self.ln2(x))
        return x

# ------------------------
# Demo script
# ------------------------

def main() -> None:
    """Run a quick forward pass to verify the setup."""
    try:
        init_distributed("nccl")
        
        # Automatically use world_size as model_parallel_size
        world_size = dist.get_world_size()
        rank = dist.get_rank()
        
        print(f"[rank {rank}] World size: {world_size}")
        initialize_model_parallel(model_parallel_size=world_size)  # Use all available ranks for TP
        
        print(f"[rank {rank}] Model parallel size: {world_size}")

        hidden = 1024
        heads = 16
        # cuda() 將模型移動到 GPU
        block = TPTransformerBlock(hidden_size=hidden, num_heads=heads, ffn_hidden_size=hidden * 4, dropout_p=0.1).cuda()

        batch, seqlen = 8, 128
        x = torch.randn(batch, seqlen, hidden, device="cuda")
        # mask: causal mask
        # (1) torch.ones(seqlen, seqlen): 創建一個 seqlen x seqlen 的矩陣，所有元素都是 1
        # (2) torch.tril(...): 建立三角矩陣，右上三角為 0，左下三角為 1。
        #     ex: [[1, 0, 0, 0, 0],
        #          [1, 1, 0, 0, 0],
        #          [1, 1, 1, 0, 0],
        #          [1, 1, 1, 1, 0],
        #          [1, 1, 1, 1, 1]]
        # (3) unsqueeze(0).unsqueeze(0): 在第 0 維和第 1 維上增加一個維度，變成 (1, 1, seqlen, seqlen)
        # (4) bool(): 將矩陣轉換為 bool 型態
        #     ex: torch.tensor([1, 0, 1]).bool() => torch.tensor([True, False, True]) => 只有 True 的元素才可見。
        # 
        # Q: 為何需要 unsqueeze(0).unsqueeze(0)?
        # A: (待驗證) attention dimension 為 (batch_size, num_heads, seqlen, seqlen)，如果使用 (S, S) 會有 shape
        # mismatch，因為 PyTorch broadcast 中要求 兩張量從右往左對齊時，每一維要麼相等、要麼有一方為 1。
        # 
        # Q: 為何需要 mask?
        # A: 在 decoder 中，使用 masked attention，避免看到未來的 token (正確答案)，如此才能
        # 學到正確的關係，例：「白日依山盡，黃河入海流」，如果沒有 mask，則會看到「黃河入海流」，
        # 如此一來，就很容易預測出「黃河入海流」，但如果使用 mask，則會看到「白日依山盡」，因此可以學到平仄押韻的關係。
        # 如果猜錯則 loss 上升，並在 backward 時，更新 weights。
        #
        # Q: 為何 mask 大小為 S x S?
        # A: 跟 scores (Q @ K^T) 大小有關，scores 大小為 (batch_size, num_heads, seqlen, seqlen)
        mask = torch.tril(torch.ones(seqlen, seqlen, device="cuda")).unsqueeze(0).unsqueeze(0).bool()
        y = block(x, mask)
        print(f"[rank {rank}] output shape: {y.shape}")
        
    finally:
        # Clean up distributed process group
        if dist.is_initialized():
            dist.destroy_process_group()

if __name__ == "__main__":
    main()
