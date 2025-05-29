package main

import (
	"context"
	"fmt"
	"time"
)

func main() {
	// 創建一個帶有取消功能的 context
	ctx, cancel := context.WithCancel(context.Background())

	// 啟動一個 goroutine 來執行任務
	go func() {
		for {
			select {
			case <-ctx.Done():
				fmt.Printf("任務被取消... 時間: %v\n", time.Now().Format("2006-01-02 15:04:05"))
				return
			default:
				fmt.Printf("執行任務中... 時間: %v\n", time.Now().Format("2006-01-02 15:04:05"))
				time.Sleep(time.Second)
			}
		}
	}()

	// 等待 3 秒後取消任務
	time.Sleep(3 * time.Second)
	fmt.Printf("準備取消任務... 時間: %v\n", time.Now().Format("2006-01-02 15:04:05"))
	cancel()

	// 等待一下讓 goroutine 有時間處理取消
	time.Sleep(time.Second)
}
