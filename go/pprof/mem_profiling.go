package main

import (
	"fmt"
	"os"
	"runtime"
	"runtime/pprof"
)

func main() {
	// 建立 profile 檔案
	f, err := os.Create("heap.prof")
	if err != nil {
		panic(err)
	}
	defer f.Close()

	// 模擬大量暫時分配（但不保留指標）
	for i := 0; i < 100000; i++ {
		processData(i)
	}

	// 手動觸發 GC，確保釋放暫存物件
	runtime.GC()

	// 寫入 heap profile
	pprof.WriteHeapProfile(f)
	fmt.Println("heap profile written to heap.prof")
}

func processData(n int) {
	// 建立 1MB 大小的暫時 slice，但不回傳也不儲存
	data := make([]byte, 1024*1024) // 1MB
	_ = data[n%len(data)]           // 防止編譯器優化掉
}
