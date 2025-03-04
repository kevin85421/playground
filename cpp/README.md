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

# std::unique_ptr<T,Deleter>::release

* [cppreference](https://en.cppreference.com/w/cpp/memory/unique_ptr/release)
  * Releases the ownership of the managed object, if any.
* 此例中，呼叫 `unique_ptr.release()` 放棄 ownership 並且返回一個 pointer，但是最後沒有 `delete pointer`，因此造成 memory leak。

```sh
g++ -fsanitize=address -g unique_ptr_release_memory_leak.cc -o memory_leak
./memory_leak

# =================================================================
# ==119563==ERROR: LeakSanitizer: detected memory leaks

# Direct leak of 4 byte(s) in 1 object(s) allocated from:
#     #0 0x7faa7e985b57 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:99
#     #1 0x558e2ecd431e in main /home/ubuntu/workspace/playground/cpp/unique_ptr_release_memory_leak.cc:5
#     #2 0x7faa7e3ba082 in __libc_start_main ../csu/libc-start.c:308

# 修正方法：加上 `delete raw_ptr;` 釋放記憶體，重新 build 就不會出錯。
```
