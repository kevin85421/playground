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

# boost::asio::thread_pool 使用 `join()` / `wait()` 的差異

* thread_pool 的 `join()` 和 `wait()` 應該是完全相同的 ([reference](https://github.com/boostorg/asio/blob/2af02fa2c817a61c30762713d791962e448e35b4/include/boost/asio/impl/thread_pool.ipp#L151))，此外使用 `join()` 之後 thread_pool 不能再提交任務。
* Ray 使用 Boost 1.81

```sh
# repo root directory
bazel run //:thread_pool_wait_and_join
```

# boost::asio::thread_pool `stop()`

* https://beta.boost.org/doc/libs/1_81_0/doc/html/boost_asio/reference/thread_pool.html
* 使用 `stop()` 之後，如果已經 `post()` 但還沒有被執行的任務，會被捨棄，但如果 thread 正在執行的任務，會繼續執行直到完成。
* 如果只有單純使用 `join()` 則會等待所有 `post()` 的任務完成。

```sh
# repo root directory
bazel run //:thread_pool_stop

# [22:30:53] Task 0 started.
# [22:30:53] Task 1 started.
# [22:30:54] Calling pool.stop()...
# [22:30:56] Task 0 finished.
# [22:30:56] Task 1 finished.
# [22:30:56] Thread pool terminated.
```

# 使用 `boost::asio::io_context` 實作 thread pool

```sh
g++ io_context_thread_pool.cc -o io_context_thread_pool -pthread
./io_context_thread_pool
```

* 在每個 thread 中呼叫 `io_context->run()`，這樣每個 thread 都會進入一個循環，不斷從 io_context 取出任務並執行。
* 只要 io_context 有任務（例如你用 post() 加進來的 lambda），這個 thread 就會執行這些任務。
* 如果沒有任務，run() 會阻塞（等待新任務），除非 work guard 被釋放或 io_context->stop() 被呼叫。

# 使用 `condition_variable` 實作 thread pool

```sh
g++ cond_var_thread_pool.cc -pthread -o cond_var_thread_pool
./cond_var_thread_pool
```

* reference: https://www.geeksforgeeks.org/thread-pool-in-cpp/

# `boost::asio::make_work_guard`

* 使用 work guard 避免 io_context 因為沒有任務而自動結束 (`io_context.run()` 返回)。而是當呼叫 `work_guard.reset()` 後 `io_context.run()` 才會返回。
* Example 1 ([without_work_guard.cc](./without_work_guard.cc))：此例子中 `io_context.run()` 會立刻返回，因為沒有任務。
  ```sh
  g++ without_work_guard.cc -pthread -o without_work_guard; ./without_work_guard
  # Output:
  before sleep 5 seconds
  before io_context run
  after io_context run
  after sleep 5 seconds
  ```
* Example 2 ([with_work_guard.cc](./with_work_guard.cc))：此例子中 `io_context.run()` 會阻塞，直到 `work_guard.reset()` 被呼叫。
  ```sh
  g++ with_work_guard.cc -pthread -o with_work_guard; ./with_work_guard
  # Output:
  before sleep 5 seconds
  before io_context run
  after sleep 5 seconds
  reset work_guard so that io_context.run() will return.
  after io_context run
  ```

# `flat_hash_map` 使用 pointer 指向 value

## 使用 normal pointer 指向 value

* 如果 map 儲存太多 elements 可能會造成 rehash，會分配更多記憶體，所有 values 的位置會改變。
* 在 `flat_hash_map_with_normal_ptr.cc` 之中，我們使用 `flat_hash_map` 並且呼叫 `rehash`，之後比較同一個 key 的 value 所對應的 address 是否相同。結果為不同。

```sh
# path: playground/
bazel run //:flat_hash_map_with_normal_ptr

# [Example output]
# Before rehash, address: 0x55581a288108
# Updated value at old address: updated value
# After rehash, address:  0x55581a289208
# Value from new address: value0
# Address changed after rehash!
# The value at the old address updated after rehash doesn't affect the value at the new address.
```

## 使用 smart pointer 指向 value

* 在 rehash 之後同一個 key 的 value 的 address 不會改變，因此可以安全地使用 pointer 指向 value。

```sh
# path: playground/
bazel run //:flat_hash_map_with_smart_ptr

# [Example output]
# Before rehash, value: value0
# Before rehash, address: 0x55c56a7c2ec0
# Before rehash, use count: 2
# After rehash, value: value0
# After rehash, address: 0x55c56a7c2ec0
# After rehash, use count: 3

# After updating via old_ptr:
# Value via old_ptr: updated value
# Value via new_ptr: updated value
# Value via map[0]: updated value

# Same object! Both pointers refer to the same memory.
```

# `boost::thread::latch`

```sh
bazel run //:boost_latch
```

* C++ `std::latch ` 是 C++ 20 才加入的 (reference: https://en.cppreference.com/w/cpp/thread)，因此我們使用 [boost::thread::latch](https://www.boost.org/doc/libs/1_81_0/doc/html/thread/synchronization.html#thread.synchronization.latches) 來實作。
* 此外 `boost::thread::latch` 也支持一些 std 沒有的功能，像是 `wait_until` 可以設定 timeout。

# `namespace`

```sh
g++ cpp_namespace.cc -o cpp_namespace
./cpp_namespace
```
* `A::hello()` 是 namespace A 中的 hello 函數。
* `::hello()` 是 global namespace中的 hello 函數。

# "returning reference to temporary"

```cpp
const std::string& GetMessage() {
    return std::string("hello world");
}
```
* `std::string("hello world")` 是一個 temporary object。
* 這個 temporary 在 GetMessage() 結束時就會被銷毀。
* 你回傳的是一個對這個已被銷毀的物件的參考（reference）。
* 在 main() 裡使用這個 reference 時，就變成了「dangling reference」
* Solution: 回傳 `const std::string` 而不是 `const std::string&`

```sh
g++ return_ref_to_temp.cc -o return_ref_to_temp
./return_ref_to_temp
```
