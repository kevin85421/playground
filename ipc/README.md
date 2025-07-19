# IPC

## Pipe

```bash
python3 pipe.py

# [Expected Output]
# Hello from child
```

* Pipe 只能從 write end 寫入，從 read end 讀取，因此稱為「單向」，可以 parent/child process 同時持有 read/write end，
所以 parent/child process 使用一個 pipe 進行雙向溝通，但這很容易出錯，因此如果希望雙向溝通 
(parent->child, child->parent)，建議使用兩個 pipes。
* 使用 `os.pipe()` 或 `pipe()` 建立的無名 pipe（unnamed pipe）只能用在：
  * parent ↔ child
  * fork 出來的 sibling process
* 適用場景：(1) Parent / Child 一對一傳遞資料 (2) 一次性、小資料傳遞。

## Shared Memory

```bash
python3 shared_mem.py
# [Expected Output]
# [父進程] 初始陣列： [0 1 2 3 4 5 6 7 8 9]
# [子進程] 原始值： [0 1 2 3 4 5 6 7 8 9]
# [子進程] 修改後： [999   1   2   3   4   5   6   7   8   9]
# [父進程] 子進程後陣列： [999   1   2   3   4   5   6   7   8   9]
```

* 使用 NumPy 是因為支持 zero copy，因此對其修改會直接反映到 shared memory。
* 適用場景：(1) 多個 process 需要共享大量資料 (2) 需要快速傳遞大量資料。
* 不適用場景：
  * 資料量小 or 傳遞頻率不高：使用 pipe、queue、socket 更簡單、更安全
  * 資料結構複雜（例如物件、文字、JSON）：Shared memory 無法直接傳遞 Python object（需序列化，反而變慢）
  * 你不想處理同步與 race condition：若多個 process 同時寫入，會出現 race condition

## Message Queue

```bash
python3 msg_queue.py
# [Expected Output]
# [Producer] 放入：0
# [Consumer] 拿到：0
# [Producer] 放入：1
# [Consumer] 拿到：1
# [Producer] 放入：2
# [Consumer] 拿到：2
# [Producer] 放入：3
# [Consumer] 拿到：3
# [Producer] 放入：4
# [Consumer] 拿到：4
# [Consumer] 收到結束訊號，退出
```

| 比較項目   | Message Queue    | Shared Memory      |
| ------ | ---------------- | ------------------ |
| 傳遞資料方式 | 一次一個 message（封包） | 多 process 存取同一記憶體區 |
| 輸入輸出同步 | 非同步（decoupled）   | 同步（通常要配 lock）      |
| 適合資料類型 | 結構化、Python 物件    | 數值陣列、影像、大型 buffer  |
| 複雜度    | 低                | 中等\~高（要管理記憶體與同步）   |
| 效能     | 中（會序列化/複製）       | 高（zero-copy）       |
| 可用性    | 內建、跨平台           | Python 3.8+ 有正式支援  |
