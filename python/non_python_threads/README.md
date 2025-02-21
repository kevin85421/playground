# Non-Python Created Threads

* https://docs.python.org/3/c-api/init.html#non-python-created-threads

## Example 1

```sh
g++ example1.cc -I/usr/include/python3.9 -lpython3.9 -lpthread -o example1
./example1

# 使用 py-spy 查看，包含兩個 threads，由於 pthread_t cpp_thread 沒有執行 Python code，
# 因此不會被 Python interpreter 管理，所以不會出現在 py-spy 的結果中。
# (1) main thread
# (2) pthread_t py_thread;
sudo env "PATH=$PATH" py-spy dump -p $PID

# [Example output]
# Process 389596: ./main
# Python v3.8.10 (/home/ubuntu/workspace/playground/python/non_python_threads/main)

# Thread 389596 (idle)
# Thread 389597 (idle)

# [Example stdout]:
# Hello from the long running cpp thread!
# Hello from the long running python thread!
# Hello from the long running cpp thread!
# Hello from the long running python thread!
# ...
```

## Example 2

```sh
g++ example2.cc -I/usr/include/python3.9 -lpython3.9 -lpthread -o example2
./example2

# 使用 py-spy 查看，此時雖然 init_python_thread 已經執行完，但是該 thread 應該仍是一個
# Python thread，因此應該看到兩個 threads。
sudo env "PATH=$PATH" py-spy dump -p $PID
```

## Example 3

* 啟動兩個 threads，在 `default_pool` 呼叫 `release_gstate` 前
  * `custom_pool` 中的 `"[C++][%s] Hello from the %s in init_python_thread"` 先印出。
  * 直到 `default_pool` 呼叫 `release_gstate` 後，GIL 被釋放，`custom_pool` 中的 `print(f'Hello from {thread_local.name}!')` 才會印出。
* Python threads 在呼叫 PyGILState_Release 後，py-spy 就看不到該 Python threads。

```sh
g++ example3.cc -I/usr/include/python3.9 -lpython3.9 -lpthread -o example3
./example3

# [C++][22:06:21.281] Hello from the custom_pool in init_python_thread
# [C++][22:06:21.280] Sleep 10 seconds
# Hello from custom_pool!
# [C++][22:06:31.281] Sleep 60 seconds
# [C++][22:06:31.281] Hello from the custom_pool in release_gstate
# [C++][22:06:31.281] Hello from the default_pool in init_python_thread
# Hello from default_pool!
# [C++][22:06:31.281] Hello from the default_pool in release_gstate
# Hello from default_pool in release_gstate!
# Hello from custom_pool in release_gstate!
```

## Example 4

* 呼叫 `PyEval_SaveThread` 釋放 GIL 並保存 thread state，並且呼叫 `PyEval_RestoreThread` 恢復 GIL 並恢復 thread state。
* https://github.com/python/cpython/issues/130394

```sh
g++ example4.cc -I/usr/include/python3.9 -lpython3.9 -lpthread -o example4
./example4

# [C++][22:02:01.658] Sleep 10 seconds
# [C++][22:02:01.658] Hello from the default_pool in init_python_thread
# Hello from default_pool, a = 1!
# sys.getswitchinterval() = 0.005
# [C++][22:02:01.658] Hello from the custom_pool in init_python_thread
# Hello from custom_pool, a = 1!
# sys.getswitchinterval() = 0.005
# [C++][22:02:11.658] Hello from the default_pool in release_gstate
# [C++][22:02:11.658] Hello from the custom_pool in release_gstate
# a = 1 in release_gstate!
# thread_local.name = default_pool in release_gstate!
# a = 1 in release_gstate!
# thread_local.name = custom_pool in release_gstate!
```
