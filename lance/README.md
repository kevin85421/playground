# Lance

## Random access benchmark: Lance vs Parquet

* 參考 [Benchmarking Random Access in Lance](https://www.lancedb.com/blog/benchmarking-random-access-in-lance)
* 為何 random access 重要：search engine、real-time feature retrieval、deep
  learning training 的 shuffle 都會大量做隨機 row 取樣。Parquet 為 columnar
  analytics 設計，random access 很慢。

### Methodology

* Dataset：N rows × `(id: int64, value: string of 1000 chars)`，blog 用 100M
  rows (~100 GB)，本機預設 1M rows。
* 1000 個 queries，每個 query 取**固定** `--rows-per-query` 個隨機 rows
  (預設 32)。Blog 用 20-50 隨機，但固定 batch 讓 per-query 數字更易解讀，且
  per-key / per-query 兩個指標等價。
* 量測三種方式：
  1. `lance.dataset.take(indices)` — Lance 原生隨機讀取。
  2. **parquet naive**：每個 query 都 `pq.read_table()` 讀整個檔案再 `take()`。
     對應 blog 中 parquet 的數字。
  3. **parquet row-group prune**：用 `ParquetFile.read_row_groups([...])` 只
     讀含目標 index 的 row groups，較公平的比較。

### Footprint

每 row ≈ 1 KB (8B id + ~1000B 隨機字串)，隨機字元幾乎無法壓縮，所以
**disk size ≈ memory size ≈ num_rows KB**：

| `--num-rows`  | pyarrow.Table | data.lance | data.parquet |
| ------------- | ------------- | ---------- | ------------ |
| 50_000        | ~50 MB        | ~50 MB     | ~50 MB       |
| 1_000_000     | ~1.0 GB       | ~970 MB    | ~960 MB      |
| 100_000_000   | ~100 GB       | ~95 GB     | ~95 GB       |

跑 100M rows (blog setup) 需要約 200 GB 可用磁碟（lance + parquet 各一份）和
能容納 100 GB Arrow Table 的 RAM。

### Run

```sh
pip install pylance pyarrow numpy

python3 random_access_benchmark.py --num-rows 1000000 --num-queries 1000

# 接近 blog 的設定（注意需要 ~100 GB 記憶體 / ~200 GB 磁碟）
python3 random_access_benchmark.py --num-rows 100000000

# 只重跑 query，不重產 dataset
python3 random_access_benchmark.py --skip-write
```

### Sample output (50k rows, MacBook, page cache warm)

```
[lance.dataset.take]
  per-query  mean  = 0.438 ms
  per-key    mean  = 12.679 us

[parquet (read whole file per query)]
  per-query  mean  = 4.208 ms
  per-key    mean  = 127.494 us

[parquet (row-group prune, group_size=5000)]
  per-query  mean  = 8.244 ms
  per-key    mean  = 246.467 us
```

* Lance 比 parquet naive 快約 10x／per-key。
* Blog 在 100M rows 報告 lance ~0.62 ms/key、parquet ~1.25 s/key（~2000x）。
  差距比本機大很多，原因是大 dataset 下：
  * Parquet naive 必須真的從 SSD 重新讀整個 100 GB；page cache 放不下。
  * Lance 使用 file footer / page index 直接 seek 到目標 page，I/O cost ≈
    O(rows requested)，而 parquet 是 O(file size)。

### 為何 row-group prune 反而比 naive 慢？

* 在小 dataset / warm cache 下，`pq.read_table()` 一次把所有 row groups 並行
  decode，而 `read_row_groups([...])` 走多次 metadata lookup + 多次 decode
  開銷不被攤銷。
* 把 `--num-rows` 加大到 GB 等級時，row-group prune 才會贏 naive，但仍遠遠
  落後 lance — 因為 row group 是 parquet 的最小讀取單位（預設 100k rows ≈
  100 MB），讀 1 個 row 也要把整個 row group decompress 完。

### Tunables

| 參數                  | 說明                                                        |
| --------------------- | ----------------------------------------------------------- |
| `--num-rows`          | dataset 大小，blog 用 `100_000_000`                         |
| `--str-len`           | 每筆 value 字串長度 (預設 1000)                             |
| `--num-queries`       | query 數量 (預設 1000)                                      |
| `--rows-per-query`    | 每個 query 取的 row 數量 (預設 32)                          |
| `--row-group-size`    | parquet row group 大小，調小可改善 parquet random access    |
| `--skip-write`        | 重用 `--data-dir` 中既有的檔案，只跑 query                  |
