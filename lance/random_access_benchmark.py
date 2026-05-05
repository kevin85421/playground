"""Benchmark random access of Lance vs Parquet.

Reference:
  https://www.lancedb.com/blog/benchmarking-random-access-in-lance

The blog uses 100M rows of 1000-char strings (~100 GB) and 1000 queries each
taking 20-50 random rows. The defaults here are smaller (1M rows) so it runs
in a reasonable time on a laptop; pass --num-rows to scale up.
"""

import argparse
import shutil
import string
import time
from pathlib import Path

import lance
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


def generate_table(num_rows: int, str_len: int, seed: int = 0) -> pa.Table:
    """Build a table of (id: int64, value: string of `str_len` chars)."""
    rng = np.random.default_rng(seed)
    alphabet = np.frombuffer(
        (string.ascii_letters + string.digits).encode(), dtype=np.uint8
    )

    flat = alphabet[rng.integers(0, len(alphabet), size=num_rows * str_len, dtype=np.int64)]
    raw = flat.tobytes()
    values = [raw[i * str_len : (i + 1) * str_len].decode() for i in range(num_rows)]

    return pa.table(
        {
            "id": pa.array(np.arange(num_rows, dtype=np.int64)),
            "value": pa.array(values, type=pa.string()),
        }
    )


def write_lance(table: pa.Table, path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    lance.write_dataset(table, str(path), mode="create")


def write_parquet(table: pa.Table, path: Path, row_group_size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    pq.write_table(table, str(path), row_group_size=row_group_size)


def bench_lance(path: Path, queries: list[np.ndarray]) -> list[float]:
    dataset = lance.dataset(str(path))
    durations = []
    for indices in queries:
        t0 = time.perf_counter()
        _ = dataset.take(indices.tolist(), columns=["value"])
        durations.append(time.perf_counter() - t0)
    return durations


def bench_parquet_naive(path: Path, queries: list[np.ndarray]) -> list[float]:
    """Read the whole file every query and `take()` from it.

    This is the "no random-access support" baseline — it's what you get with a
    plain `pq.read_table()` and matches the blog's parquet number.
    """
    durations = []
    for indices in queries:
        t0 = time.perf_counter()
        table = pq.read_table(str(path), columns=["value"])
        _ = table.take(pa.array(indices))
        durations.append(time.perf_counter() - t0)
    return durations


def bench_parquet_row_group(path: Path, queries: list[np.ndarray]) -> list[float]:
    """Only read the row groups that contain the requested indices.

    A fairer comparison: parquet can prune row groups, but it still has to read
    the full row group for each requested row.
    """
    pf = pq.ParquetFile(str(path))
    rg_starts = np.zeros(pf.num_row_groups + 1, dtype=np.int64)
    for i in range(pf.num_row_groups):
        rg_starts[i + 1] = rg_starts[i] + pf.metadata.row_group(i).num_rows

    durations = []
    for indices in queries:
        t0 = time.perf_counter()
        per_idx_rg = np.searchsorted(rg_starts, indices, side="right") - 1
        rg_ids = np.unique(per_idx_rg)
        table = pf.read_row_groups(rg_ids.tolist(), columns=["value"])
        # offset of each picked row group within the concatenated read result
        cursor_in_read = {}
        cursor = 0
        for rg in rg_ids:
            cursor_in_read[int(rg)] = cursor
            cursor += int(rg_starts[rg + 1] - rg_starts[rg])
        local = np.array(
            [
                cursor_in_read[int(rg)] + int(idx - rg_starts[rg])
                for idx, rg in zip(indices, per_idx_rg)
            ]
        )
        _ = table.take(pa.array(local))
        durations.append(time.perf_counter() - t0)
    return durations


def summarize(name: str, durations: list[float], rows_per_query: np.ndarray) -> None:
    arr = np.array(durations)
    per_key = arr / rows_per_query
    print(f"\n[{name}]")
    print(f"  queries          = {len(arr)}")
    print(f"  total rows taken = {rows_per_query.sum()}")
    print(f"  per-query  mean  = {arr.mean()*1000:.3f} ms")
    print(f"  per-query  p50   = {np.percentile(arr, 50)*1000:.3f} ms")
    print(f"  per-query  p95   = {np.percentile(arr, 95)*1000:.3f} ms")
    print(f"  per-query  p99   = {np.percentile(arr, 99)*1000:.3f} ms")
    print(f"  per-key    mean  = {per_key.mean()*1e6:.3f} us")
    print(f"  per-key    p50   = {np.percentile(per_key, 50)*1e6:.3f} us")


def main() -> None:
    ap = argparse.ArgumentParser()
    # Each row is ~1 KB (8B int64 id + ~1000B string), and random alphanumeric
    # strings barely compress — so disk and in-memory size both ~= num_rows KB.
    # Defaults: 1M rows -> ~1 GB on disk for each format, ~1 GB in pyarrow.Table.
    # Blog setup (100M rows) -> ~100 GB; need a roomy SSD + RAM to reproduce.
    ap.add_argument("--num-rows", type=int, default=1_000_000,
                    help="dataset size (blog uses 100_000_000; ~1 KB per row)")
    ap.add_argument("--str-len", type=int, default=1000,
                    help="length of the random string per row")
    ap.add_argument("--num-queries", type=int, default=1000)
    ap.add_argument("--rows-per-query", type=int, default=32,
                    help="rows taken per query (blog uses random 20-50)")
    ap.add_argument("--row-group-size", type=int, default=100_000,
                    help="parquet row group size (smaller = better random access)")
    ap.add_argument("--data-dir", type=Path, default=Path("/tmp/lance_bench"))
    ap.add_argument("--skip-write", action="store_true",
                    help="reuse existing files in --data-dir")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    args.data_dir.mkdir(parents=True, exist_ok=True)
    lance_path = args.data_dir / "data.lance"
    parquet_path = args.data_dir / "data.parquet"

    if not args.skip_write:
        print(f"generating {args.num_rows:,} rows of {args.str_len}-char strings...")
        t0 = time.perf_counter()
        table = generate_table(args.num_rows, args.str_len, seed=args.seed)
        print(f"  generate: {time.perf_counter()-t0:.2f}s "
              f"(in-memory size ~ {table.nbytes/1e9:.2f} GB)")

        t0 = time.perf_counter()
        write_lance(table, lance_path)
        print(f"  write lance:   {time.perf_counter()-t0:.2f}s -> {lance_path}")

        t0 = time.perf_counter()
        write_parquet(table, parquet_path, row_group_size=args.row_group_size)
        print(f"  write parquet: {time.perf_counter()-t0:.2f}s -> {parquet_path}")

    rng = np.random.default_rng(args.seed + 1)
    rows_per_query = np.full(args.num_queries, args.rows_per_query, dtype=np.int64)
    queries = [
        np.sort(rng.choice(args.num_rows, size=args.rows_per_query, replace=False))
        for _ in range(args.num_queries)
    ]

    print(f"\nrunning {args.num_queries} queries x {args.rows_per_query} rows each "
          f"(total {args.num_queries * args.rows_per_query:,} rows)...")

    summarize("lance.dataset.take",
              bench_lance(lance_path, queries), rows_per_query)
    summarize("parquet (read whole file per query)",
              bench_parquet_naive(parquet_path, queries), rows_per_query)
    summarize(f"parquet (row-group prune, group_size={args.row_group_size})",
              bench_parquet_row_group(parquet_path, queries), rows_per_query)


if __name__ == "__main__":
    main()
