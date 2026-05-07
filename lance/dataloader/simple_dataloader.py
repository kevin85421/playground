"""Minimal Lance training data pipeline (no framework binding).

Reference: https://docs.lancedb.com/training

Shows the recommended `permutation_builder` workflow:

  source table
   |
   |  permutation_builder(table)
   |    .filter(...)                # optional row predicate
   |    .shuffle(seed=...)          # randomize row order
   |    .split_random(ratios=..., split_names=...)
   |    .execute()                  # -> permutation table (LanceTable)
   v
  Permutation.from_tables(src, perm_table, split=...)
   .select_columns(...)             # column projection
   .with_batch_size(...)            # batch size for iteration
   .with_format(...)                # python / numpy / pandas / arrow / torch

Compared with `torch_dataloader.py`, this version skips the PyTorch wrapper
entirely — `Permutation.__iter__` is enough for plain Python training loops.

Run:
    pip install lancedb pyarrow
    python3 simple_dataloader.py
"""

import lancedb
import pyarrow as pa
from lancedb.permutation import Permutation, permutation_builder


def main() -> None:
    # 1. Source table
    db = lancedb.connect("/tmp/lance_train_demo")
    if "demo" in db.list_tables().tables:
        db.drop_table("demo")
    table = db.create_table(
        "demo",
        pa.table(
            {
                "id": list(range(20)),
                "score": [i * 0.1 for i in range(20)],
            }
        ),
    )

    # 2. Build a permutation: shuffle + 80/20 train/val split
    perm_table = (
        permutation_builder(table)
        .shuffle(seed=42)
        .split_random(ratios=[0.8, 0.2], split_names=["train", "val"])
        .execute()
    )

    # 3. Wrap as Permutation per split, configure column projection + batching
    def make_loader(split: str) -> Permutation:
        return (
            Permutation.from_tables(table, perm_table, split=split)
            .select_columns(["id", "score"])
            .with_batch_size(4)
            .with_format("python")  # dict of column -> list of values
        )

    train = make_loader("train")
    val = make_loader("val")
    print(f"train rows = {len(train)}, val rows = {len(val)}")

    # 4. Iterate
    for name, loader in [("train", train), ("val", val)]:
        print(f"\n--- {name} ---")
        for i, batch in enumerate(loader):
            print(f"  batch {i}: {batch}")


if __name__ == "__main__":
    main()
