# pprof

[pprof](https://github.com/google/pprof/blob/main/doc/README.md#details) 是用來分析 / 視覺化 profiling data 的工具。

## Memory profiling

[mem_profiling.go](./mem_profiling.go) 是 memory profiling 的範例。

```bash
go build -o mem_profiling mem_profiling.go
# 執行 mem_profiling 後，會在當前目錄生成 heap.prof 檔案
./mem_profiling
# 使用 pprof 視覺化 heap.prof 檔案
go tool pprof -alloc_space ./mem_profiling heap.prof

# 在 pprof 介面中輸入 `top`
top

# (pprof) top
# Showing nodes accounting for 97.50GB, 100% of 97.50GB total
# Dropped 3 nodes (cum <= 0.49GB)
#       flat  flat%   sum%        cum   cum%
#    97.50GB   100%   100%    97.50GB   100%  main.processData (inline)
#          0     0%   100%    97.50GB   100%  main.main
#          0     0%   100%    97.50GB   100%  runtime.main
```

其中 `alloc_space` 是列出 allocated memory 的資訊，而 allocated memory 包含已經被 GC 釋放的 memory，以及尚未被 GC 釋放的 live memory。因此就算很高也未必會造成 OOM。
