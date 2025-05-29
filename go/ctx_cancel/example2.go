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
		// 模擬一個耗時的任務
		fmt.Printf("開始執行耗時任務... 時間: %v\n", time.Now().Format("2006-01-02 15:04:05"))
		time.Sleep(15 * time.Second) // 這個任務會執行 15 秒
		fmt.Printf("任務完成... 時間: %v\n", time.Now().Format("2006-01-02 15:04:05"))

		// 檢查 context 是否被取消
		select {
		case <-ctx.Done():
			fmt.Println("任務被取消")
			return
		default:
			fmt.Println("任務完成")
		}
	}()

	// 等待 2 秒後取消任務
	time.Sleep(2 * time.Second)
	fmt.Printf("準備取消任務... 時間: %v\n", time.Now().Format("2006-01-02 15:04:05"))
	cancel()

	// 等待一下讓 goroutine 有時間處理取消
	time.Sleep(30 * time.Second)
}
