# Context Cancel

```sh
go run example1.go
# 執行任務中... 時間: 2025-05-29 22:27:54
# 執行任務中... 時間: 2025-05-29 22:27:55
# 執行任務中... 時間: 2025-05-29 22:27:56
# 執行任務中... 時間: 2025-05-29 22:27:57
# 準備取消任務... 時間: 2025-05-29 22:27:57
# 任務被取消... 時間: 2025-05-29 22:27:58
```
* Sleep 三秒後呼叫 `cancel()`，由於此時 goroutine 也在等待 `ctx.Done()`，所以會立即取消。

```sh
go run example2.go
# 開始執行耗時任務... 時間: 2025-05-29 22:28:36
# 準備取消任務... 時間: 2025-05-29 22:28:38
# 任務完成... 時間: 2025-05-29 22:28:51
# 任務被取消
```
* 雖然 `cancel()` 被呼叫了，但由於 goroutine 在 `time.Sleep(15 * time.Second)`，因此得等到 15 秒後 goroutine 開始檢查 `ctx.Done()` 才會被取消。