"""Minimal PyTorch DataLoader on top of a LanceDB table.

Reference: https://docs.lancedb.com/training/torch

Note: as of lancedb 0.27.1, `Permutation.__getitem__` returns None — so feeding
a Permutation straight into `torch.utils.data.DataLoader` (as the doc shows)
does not actually work. Two failure modes:

  * `DataLoader(permutation)`                 -> TypeError on default_collate
  * `DataLoader(permutation, batch_size=None)` -> silently yields None forever

This is tracked in https://github.com/lancedb/lancedb/issues/2996 and was
fixed by https://github.com/lancedb/lancedb/pull/3013, but at time of writing
the fix has not been released to PyPI (latest is 0.27.1; 0.28+ should have it).

Until then, the workaround below is a thin `IterableDataset` that delegates
to `Permutation.__iter__` — which IS implemented and yields real batches.
With `batch_size=None`, DataLoader forwards the already-batched output
untouched.

Once 0.28 lands and this is fixed upstream, the wrapper should no longer be
needed and you can pass the Permutation directly per the official doc.

Run:
    pip install lancedb torch pyarrow
    python3 torch_dataloader.py
"""

import lancedb
import pyarrow as pa
import torch
from lancedb.permutation import Permutation
from torch.utils.data import DataLoader, IterableDataset


class LancePermutationDataset(IterableDataset):
    """Adapt a LanceDB Permutation to torch's IterableDataset protocol.

    Workaround for https://github.com/lancedb/lancedb/issues/2996
    (fixed in https://github.com/lancedb/lancedb/pull/3013, awaiting 0.28
    release on PyPI). Drop this class once you've upgraded past the fix.
    """

    def __init__(self, permutation: Permutation) -> None:
        self.permutation = permutation

    def __iter__(self):
        return iter(self.permutation)


def main() -> None:
    # 1. Create / overwrite a LanceDB database + table
    db = lancedb.connect("/tmp/lance_torch_demo")
    # list_tables() returns a ListTablesResponse with .tables attribute (not a list)
    if "demo" in db.list_tables().tables:
        db.drop_table("demo")
    table = db.create_table(
        "demo",
        pa.table(
            {
                "id": list(range(1000)),
                "score": [i * 0.001 for i in range(1000)],
            }
        ),
    )

    # 2. Build a Permutation (the recommended pattern from the doc):
    #    - select_columns:   only read the columns we need
    #    - with_batch_size:  batch size is set on the Permutation, not DataLoader
    #    - with_format:      "torch" returns a 2D tensor (num_columns, batch_size).
    #                        Only numeric columns are supported. For mixed schemas
    #                        use "python" / "numpy" / "pandas" / "arrow".
    permutation = (
        Permutation.identity(table)
        .select_columns(["id", "score"])
        .with_batch_size(4)
        .with_format("torch")
    )

    # 3. Wrap and feed to DataLoader. batch_size=None keeps DataLoader from
    #    re-batching what Permutation already produced.
    loader = DataLoader(LancePermutationDataset(permutation), batch_size=None)

    # 4. Iterate
    #
    # batch 0: type=Tensor, shape=(2, 4), dtype=torch.float64
    # tensor([[0.0000e+00, 1.0000e+00, 2.0000e+00, 3.0000e+00], => "id" column
    #         [0.0000e+00, 1.0000e-03, 2.0000e-03, 3.0000e-03]], dtype=torch.float64) => "score" column
    # batch 1: type=Tensor, shape=(2, 4), dtype=torch.float64
    # tensor([[4.0000e+00, 5.0000e+00, 6.0000e+00, 7.0000e+00],
    #         [4.0000e-03, 5.0000e-03, 6.0000e-03, 7.0000e-03]], dtype=torch.float64)
    # batch 2: type=Tensor, shape=(2, 4), dtype=torch.float64
    # tensor([[8.0000e+00, 9.0000e+00, 1.0000e+01, 1.1000e+01],
    #         [8.0000e-03, 9.0000e-03, 1.0000e-02, 1.1000e-02]], dtype=torch.float64)
    for i, batch in enumerate(loader):
        print(
            f"batch {i}: type={type(batch).__name__}, "
            f"shape={tuple(batch.shape)}, dtype={batch.dtype}"
        )
        print(batch)
        if i >= 2:
            break


if __name__ == "__main__":
    main()
