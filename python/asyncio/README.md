# Asyncio

## coroutine / `async def` / `await` / `asyncio.run` / `asyncio.gather`

```bash
python countasync.py
# [Example Output]
# One
# One
# One
# Two
# Two
# Two
# countasync.py executed in 1.00 seconds.
```

* [countasync.py](./countasync.py) 來源於 [Real Python](https://realpython.com/async-io-python/)
* Coroutine（協程 `async def`）(ChatGPT 回答)
  * 是一種可以「暫停」和「恢復」執行的函數。
  * 和一般函數不一樣，協程可以在中間 yield 或 await 某些事情（例如等待 I/O），然後讓出控制權給其他任務執行，等資料準備好之後再繼續執行。
  * 簡單來說，協程是一種「更聰明的函數」，它不會一口氣跑完，而是能被調度器（例如 asyncio 的 event loop）中斷、掛起與恢復。

* [asyncio.run(main())](https://docs.python.org/3/library/asyncio-runner.html#asyncio.run)
  * 執行 coroutine (在此為 `main()` 函數)，並回傳結果。
  * 如果此 thread 已經有其他 asyncio event loop，`asyncio.run()` 不能再被呼叫。 
  * 管理 event loop。

* `asyncio.gather(count(), count(), count())`：
  * `gather` 會「同時」啟動三個 coroutines，並且回傳一個 `awaitable`，使用 `await` 來等待三個 coroutine 完成。
  * 如果使用 `await count(); await count(); await count()` 則是串行執行，會等待第一個 coroutine 完成，再執行第二個，最後執行第三個。

## `asyncio.Queue()`

```bash
# 產生 2 個 producer，5 個 consumer，然後透過 asyncio.Queue() 來進行資料傳遞。
python3 asyncq.py -p 2 -c 5
```

* [asyncq.py](./asyncq.py) 來源於 [Real Python](https://realpython.com/async-io-python/)
* `asyncio.Queue`
  * `q = asyncio.Queue()` 初始化
  * `await q.put(item)` 將 item 放入 queue
  * `item = await q.get()` 從 queue 中取出 item
  * `q.task_done()` 表示 item 已經被處理完畢
  * `await q.join()` 等待 queue 中的所有 item 都被處理完畢
    * 每個 `q.get()` 都需要一個對應的 `q.task_done()`，不然 `await q.join()` 會一直等待。
* `asyncio.create_task(produce(n, q))` 回傳 Task
  * 把一個 coroutine 變成 Task 並送去 event loop 執行，並且可以之後再 `await`。
  * `gather` 則是會同時啟動多個 tasks，並且立刻開始等。
* `task.cancel()` 取消 task

## 常見錯誤：在 async function 中使用 blocking code

```bash
python3 blocking_async.py
# Start
# End
# Start
# End
# Time taken: 6.006925582885742 seconds
```

* 在其中使用 `time.sleep(3)` 會導致 event loop 卡住無法運行其他 coroutine。

## `asyncio.wait_for(coro, timeout)` 設定 timeout

```bash
python3 async_wait_for.py
```

* https://docs.python.org/3/library/asyncio-task.html#asyncio.wait_for
* `timeout` 到的話 cancel tasks，並且丟出 `TimeoutError` (Python 3.11)。`asyncio_wait_for` 會等到所有 future 都被 cancel，因此等待的時間可能會超過 `timeout`。

## Event loop overhead

```bash
python3 benchmark_event_loop_overhead.py
# [Example Output]
# Average event loop creation overhead: 0.0078 ms
# Average event loop closing overhead: 0.0034 ms
```
* 測試：`loop = asyncio.new_event_loop()` 和 `loop.close()` 的 overhead。

## `__aenter__` and `__aexit__`

```bash
python3 async_context.py
# [Example Output]
# This should be printed before the __aenter__
# __aenter__: Setting up resource1
# Using resource1 => This should be printed after __aenter__ and before __aexit__
# __aexit__: Cleaning up resource1
# This should be printed after the __aexit__
```

* `async with` 會自動呼叫 `__aenter__` 和 `__aexit__`。
* Ref: https://docs.python.org/3/reference/datamodel.html#asynchronous-context-managers