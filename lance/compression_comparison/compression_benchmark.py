"""Compare file size + random-access speed: Parquet vs Lance 2.0 vs Lance 2.1.

Uses a deliberately compressible schema (sorted IDs, low-cardinality categoricals,
repeated values) so Parquet's dictionary + RLE + delta encoding can shine. The
goal is to show the storage / speed trade-off, not the random-string scenario
where Lance and Parquet are roughly tied.

Schema:
  - id          : int64, sorted/monotonic            -> Parquet delta encoding
  - status      : string, 5 values                   -> dict + RLE
  - country     : string, 50 values                  -> dict
  - category    : string, 10 values                  -> dict + RLE
  - event_count : int32, small values 0-9 repeating  -> RLE / bitpacking
  - is_active   : bool                               -> RLE
"""

import argparse
import shutil
import time
from pathlib import Path

import lance
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


def generate_table(num_rows: int, seed: int = 0) -> pa.Table:
    rng = np.random.default_rng(seed)
    ids = np.arange(num_rows, dtype=np.int64)
    statuses = ["active", "inactive", "pending", "deleted", "archived"]
    countries = [f"C{i:02d}" for i in range(50)]
    categories = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    return pa.table(
        {
            "id": ids,
            "status": pa.array([statuses[i] for i in rng.integers(0, len(statuses), num_rows)]),
            "country": pa.array([countries[i] for i in rng.integers(0, len(countries), num_rows)]),
            "category": pa.array([categories[i] for i in rng.integers(0, len(categories), num_rows)]),
            "event_count": pa.array(rng.integers(0, 10, num_rows, dtype=np.int32)),
            "is_active": pa.array(rng.integers(0, 2, num_rows, dtype=np.bool_)),
        }
    )


def write_parquet(table: pa.Table, path: Path, row_group_size: int) -> None:
    if path.exists():
        path.unlink()
    pq.write_table(table, str(path), compression="snappy", row_group_size=row_group_size)


def write_lance(table: pa.Table, path: Path, version: str) -> None:
    if path.exists():
        shutil.rmtree(path)
    lance.write_dataset(table, str(path), data_storage_version=version)


def dir_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def bench_lance(path: Path, queries: list[np.ndarray], columns: list[str]) -> list[float]:
    dataset = lance.dataset(str(path))
    durations = []
    for indices in queries:
        t0 = time.perf_counter()
        _ = dataset.take(indices.tolist(), columns=columns)
        durations.append(time.perf_counter() - t0)
    return durations


def bench_parquet(path: Path, queries: list[np.ndarray], columns: list[str]) -> list[float]:
    """Read whole file each query and `take()` — matches the random_access_benchmark baseline."""
    durations = []
    for indices in queries:
        t0 = time.perf_counter()
        table = pq.read_table(str(path), columns=columns)
        _ = table.take(pa.array(indices))
        durations.append(time.perf_counter() - t0)
    return durations


def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--num-rows", type=int, default=1_000_000)
    ap.add_argument("--num-queries", type=int, default=1000)
    ap.add_argument("--rows-per-query", type=int, default=32)
    ap.add_argument("--row-group-size", type=int, default=100_000)
    ap.add_argument("--data-dir", type=Path, default=Path("/tmp/lance_compression_bench"))
    ap.add_argument("--columns", nargs="+", default=["status", "country", "category", "event_count"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--skip-write", action="store_true")
    args = ap.parse_args()

    args.data_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "parquet (snappy)": args.data_dir / "data.parquet",
        "lance 2.0": args.data_dir / "data_v2_0.lance",
        "lance 2.1": args.data_dir / "data_v2_1.lance",
    }

    if not args.skip_write:
        print(f"generating {args.num_rows:,} rows of compressible schema...")
        t0 = time.perf_counter()
        table = generate_table(args.num_rows, seed=args.seed)
        print(f"  generate: {time.perf_counter()-t0:.2f}s "
              f"(in-memory ~{table.nbytes/1e6:.1f} MB)\n")

        for name, path in paths.items():
            t0 = time.perf_counter()
            if name.startswith("parquet"):
                write_parquet(table, path, row_group_size=args.row_group_size)
            elif name == "lance 2.0":
                write_lance(table, path, version="2.0")
            elif name == "lance 2.1":
                write_lance(table, path, version="2.1")
            print(f"  write {name:18s}: {time.perf_counter()-t0:.2f}s -> {fmt_bytes(dir_size(path))}")

    rng = np.random.default_rng(args.seed + 1)
    queries = [
        np.sort(rng.choice(args.num_rows, size=args.rows_per_query, replace=False))
        for _ in range(args.num_queries)
    ]
    rows_per_query = np.full(args.num_queries, args.rows_per_query, dtype=np.int64)

    print(f"\nrunning {args.num_queries} queries x {args.rows_per_query} rows each "
          f"(reading columns: {args.columns})\n")

    results = {}
    for name, path in paths.items():
        if name.startswith("parquet"):
            durations = bench_parquet(path, queries, args.columns)
        else:
            durations = bench_lance(path, queries, args.columns)
        per_key_us = (np.array(durations) / rows_per_query).mean() * 1e6
        results[name] = (dir_size(path), per_key_us)

    print(f"{'format':<20s} {'size':>12s}  {'per-key mean':>15s}")
    print("-" * 52)
    for name, (size, per_key_us) in results.items():
        print(f"{name:<20s} {fmt_bytes(size):>12s}  {per_key_us:>12.2f} µs")

    parquet_size = results["parquet (snappy)"][0]
    print()
    for name, (size, _) in results.items():
        if name == "parquet (snappy)":
            continue
        print(f"  {name} / parquet size  = {size / parquet_size:.2f}x")


if __name__ == "__main__":
    main()
