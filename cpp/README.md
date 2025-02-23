# std::function

* 一個 function 回傳一個 function

```sh
g++ std_function.cc
./a.out
```

# boost::asio::thread_pool

```sh
g++ -pthread thread_pool.cc -o thread_pool
THREAD_POOL_SIZE=0 ./thread_pool

# Output: pool.join() 會立刻返回，因為沒有任何 thread 在 pool 中
Thread pool size: 0
Program execution finished.

THREAD_POOL_SIZE=1 ./thread_pool

# Output: pool.join() 會等待 thread 完成工作
Thread pool size: 1
This task will be executed because there are threads in the thread pool.
Program execution finished.
```