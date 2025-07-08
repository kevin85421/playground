# [countasync.py](./countasync.py)

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