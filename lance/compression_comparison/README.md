# Compression comparison: Parquet vs Lance 2.0 vs Lance 2.1

呼應上層 `random_access_benchmark`。前者用 1000-char 隨機字串 → parquet 和
lance 大小幾乎一樣（隨機資料無法壓縮）。這個 benchmark 反過來：故意挑
**高度可壓縮的 schema**，看 lance 2.0 多大、lance 2.1 怎麼追上 parquet。

## Schema (deliberately compressible)

| Column | Type | 為何容易壓 |
|---|---|---|
| `id`          | int64, 排序遞增      | parquet delta encoding |
| `status`      | string, 5 種值       | dict + RLE             |
| `country`     | string, 50 種值      | dict                   |
| `category`    | string, 10 種值      | dict + RLE             |
| `event_count` | int32, 0-9 重複值    | RLE / bitpacking       |
| `is_active`   | bool                 | RLE                    |

## Run

```sh
python3 compression_benchmark.py --num-rows 1000000 --num-queries 1000
```

## Sample output (1M rows)

```
generating 1,000,000 rows of compressible schema...
  generate: 0.12s (in-memory ~35.3 MB)

  write parquet (snappy)  : 0.08s -> 8.0 MB
  write lance 2.0         : 0.39s -> 14.4 MB
  write lance 2.1         : 0.03s -> 8.8 MB

format                       size     per-key mean
----------------------------------------------------
parquet (snappy)           8.0 MB         96.93 µs
lance 2.0                 14.4 MB         21.41 µs
lance 2.1                  8.8 MB         20.04 µs

  lance 2.0 / parquet size  = 1.80x
  lance 2.1 / parquet size  = 1.10x
```

## Takeaway

| 方面 | Parquet (snappy) | Lance 2.0 | Lance 2.1 |
|---|---|---|---|
| 大小 | **8.0 MB** ⭐ | 14.4 MB (1.80x) | 8.8 MB (1.10x) |
| Random access | 96.93 µs/key | 21.41 µs/key (4.5x faster) | **20.04 µs/key** ⭐ (4.8x faster) |

* **Lance 2.0** 在 storage 上有明顯劣勢（~1.8x parquet）—— 這是設計取捨：
  random access 友善的 page layout 無法和 parquet 一樣激進的壓縮。
* **Lance 2.1** 加了 FSST（string）、bitpacking（int）、更好的 dictionary
  encoding 等 column-level encoding，把 storage 差距壓到 ~1.1x，同時
  random access 還更快。
* 對 categorical / sorted / repeated 為主的 schema，**lance 2.1 基本上
  消除了 storage 劣勢**。隨機字串 / float embedding 等 incompressible data
  則三者大小本來就差不多。

## 為何不在 random_access_benchmark 用這個 schema？

* 上層 benchmark 主要是要展示 **random access 速度**，schema 用 1000-char
  隨機字串目的是讓「I/O cost」單一化、可控、易解讀（每 row ~1 KB）。
* 如果用這裡的 6-column schema，per-row size 太小（~35 bytes），page cache
  完全主導，反而看不出 lance / parquet 的本質差異。
* 兩個 benchmark 互補：random access 速度看上層、storage trade-off 看這裡。
