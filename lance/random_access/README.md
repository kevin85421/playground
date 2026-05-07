# Lance

## Random access benchmark: Lance vs Parquet

* 參考 [Benchmarking Random Access in Lance](https://www.lancedb.com/blog/benchmarking-random-access-in-lance)
* 為何 random access 重要：search engine、real-time feature retrieval、deep
  learning training 的 shuffle 都會大量做隨機 row 取樣。Parquet 為 columnar
  analytics 設計，random access 很慢。

### Methodology

* Dataset：N rows × `(id: int64, small: int32, value: string of 1000 chars)`，
  blog 用 100M rows (~100 GB)，本機預設 1M rows。`small` (~4B) 用來對比
  「讀小 column」 vs 「讀大 column」的隨機存取成本。
* 1000 個 queries，每個 query 取**固定** `--rows-per-query` 個隨機 rows
  (預設 32)。Blog 用 20-50 隨機，但固定 batch 讓 per-query 數字更易解讀，且
  per-key / per-query 兩個指標等價。
* 量測三種方式 × 兩個 column (`value` / `small`)：
  1. `lance.dataset.take(indices)` — Lance 原生隨機讀取。
  2. **parquet naive**：每個 query 都 `pq.read_table()` 讀整個檔案再 `take()`。
     對應 blog 中 parquet 的數字。
  3. **parquet row-group prune**：用 `ParquetFile.read_row_groups([...])` 只
     讀含目標 index 的 row groups，較公平的比較。

### Run

```sh
pip install pylance pyarrow numpy

python3 random_access_benchmark.py --num-rows 1000000 --num-queries 1000

# 接近 blog 的設定（注意需要 ~100 GB 記憶體 / ~200 GB 磁碟）
python3 random_access_benchmark.py --num-rows 100000000

# 只重跑 query，不重產 dataset
python3 random_access_benchmark.py --skip-write
```

### Sample output (MacBook)

```sh
# 1M rows, 1000 char/row, 1000 queries, 32 rows/query
python3 random_access_benchmark.py --num-rows 1000000 --num-queries 1000

# [Example output, per-key mean only]
generating 1,000,000 rows of 1000-char strings...
  generate: 2.96s (in-memory size ~ 1.02 GB)
  write lance:   0.16s -> /tmp/lance_bench/data.lance
  write parquet: 0.22s -> /tmp/lance_bench/data.parquet

========== column = 'value' (~1000B/row) ==========
[lance.dataset.take]                              per-key mean = 14.417 us
[parquet (read whole file per query)]             per-key mean = 10241.129 us
[parquet (row-group prune, group_size=100000)]    per-key mean = 5915.047 us

========== column = 'small' (4B/row) ==========
[lance.dataset.take]                              per-key mean = 7.491 us
[parquet (read whole file per query)]             per-key mean = 21.786 us
[parquet (row-group prune, group_size=100000)]    per-key mean = 25.479 us
```

#### 讀大 column (`value`, ~1000B/row)

* Lance 比 parquet naive 快 **~710x**／per-key (14.4 µs vs 10.2 ms)，比 row-group
  prune 快 **~410x**。
* Blog 在 100M rows 報告 lance ~620 µs/key、parquet ~1.25 s/key（~2000x）。本
  機 1M 看到的 ~710x 比 blog 小，因為 1M dataset (~1 GB) 還能塞進 page cache，
  parquet naive 第二次以後讀的是記憶體；100M (~100 GB) 必須真的回 SSD。
* 根本原因是 I/O 複雜度不同，dataset 越大差距越大：
  * Parquet naive: O(file size) — 每個 query 重讀整檔。
  * Parquet row-group prune: O(row_group_size × queries) — Parquet 規格上最小
    壓縮單位是 page (~1 MB)，但 pyarrow 的 `read_row_groups()` 會 decompress
    整個 column chunk（也就是該 row group 內目標 column 的所有 pages），所以
    讀 1 row 仍要 decompress 整個 row group 的 column chunk (~100 MB)。
    Parquet 有 page index + offset index 可做 page-level pruning，但 pyarrow
    對 random row take 沒有公開 API。
  * Lance: O(rows requested) — 透過 file footer / page index 直接 seek 到目標
    page，跟 dataset 大小無關。

#### 讀小 column (`small`, 4B/row)

* Lance 比 parquet 只快 **~3x**（7.5 µs vs 22-25 µs），差距從讀 `value` 時的
  ~700x 急縮。
* 為何縮小：parquet 的 **column pruning** 真的會跳過 `value` 那一大坨資料，
  decompress 成本與目標 column 大小成正比，從 1000B → 4B 等於縮 250x。
* Lance 也變快（每 row 讀的少），但 per-row seek 本身的固定 overhead 在小
  column 下顯露出來。
* **Practical implication**：如果你的 random-access workload 只挑某個小
  column（metadata、ID、score），parquet 不會輸 lance 太多 — **3x 而不是
  700x**。Schema 設計上把熱常被 random-access 的小 metadata 跟冷的大 blob
  分開存，可以讓 parquet 撐住這類 workload。讀大 column（embedding、image
  bytes、長 text）—— lance 的優勢無可取代。

### Naive vs row-group prune crossover

* 50k rows：naive 較快（whole-file decode 比多次 metadata lookup 划算）。
* 1M rows：prune 較快（重讀整檔的成本超過 prune 的 bookkeeping）。
* 兩者都遠落後 lance —— 原因如上：pyarrow `read_row_groups()` 實際上 decompress
  整個 column chunk，雖然 Parquet 規格上最小壓縮單位是 page。

### Tunables

| 參數                  | 說明                                                        |
| --------------------- | ----------------------------------------------------------- |
| `--num-rows`          | dataset 大小，blog 用 `100_000_000`                         |
| `--str-len`           | 每筆 value 字串長度 (預設 1000)                             |
| `--num-queries`       | query 數量 (預設 1000)                                      |
| `--rows-per-query`    | 每個 query 取的 row 數量 (預設 32)                          |
| `--row-group-size`    | parquet row group 大小，調小可改善 parquet random access    |
| `--skip-write`        | 重用 `--data-dir` 中既有的檔案，只跑 query                  |
