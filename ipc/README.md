# IPC

## Pipe

```bash
python3 pipe.py
```

* Pipe 只能從 write end 寫入，從 read end 讀取，因此稱為「單向」，可以 parent/child process 同時持有 read/write end，
所以 parent/child process 使用一個 pipe 進行雙向溝通，但這很容易出錯，因此如果希望雙向溝通 
(parent->child, child->parent)，建議使用兩個 pipes。
* 使用 `os.pipe()` 或 `pipe()` 建立的無名 pipe（unnamed pipe）只能用在：
  * parent ↔ child
  * fork 出來的 sibling process
* 適用場景：(1) Parent / Child 一對一傳遞資料 (2) 一次性、小資料傳遞。