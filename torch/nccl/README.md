# `dist.destroy_process_group()`

* 建立兩個 process，rank 0 是 receiver，rank 1 是 sender。
* 但是 sender 不會呼叫 `send`，而是 30 秒後呼叫 `destroy_process_group`。
* receiver 有兩個 threads，其中 main thread 呼叫 `recv`，另一個 thread 在 45 秒後呼叫 `destroy_process_group`。
* 此實驗要驗證是否 `destroy_process_group` 呼叫後是否 `recv` 會 unblock。結果並不會。

```bash
(base) ➜  nccl git:(main) ✗ python3 destroy_comm.py
Rank 0 starting at time: 2025-08-12 00:36:22
Rank 1 starting at time: 2025-08-12 00:36:22
Rank 1 sleeping and skipping send...
Rank 0 waiting to receive...
Rank 1 destroying process group without sending.
Rank 0 destroying process group from thread after 45s.
# hang...
```