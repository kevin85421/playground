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

## Example 5

* https://github.com/python/cpython/issues/130394#issuecomment-2676346729
  * Python 社群說就算沒有 PyEval_SaveThread 過了 switch interval 後 GIL 仍該被釋放。
  * 表現如同上方所述，但是有時候 Python 的 log 會在 10 秒後才印出，不知為何。 

```sh
g++ example5.cc -I/usr/include/python3.9 -lpython3.9 -lpthread -o example5
./example5

# [C++][00:41:02.663] Sleep 10 seconds
# [C++][00:41:02.663] Hello from the default_pool in init_python_thread
# [C++][00:41:02.663] Hello from the custom_pool in init_python_thread
# [Python][00:41:02.664] Hello from default_pool, a = 1!
# [Python][00:41:02.664] sys.getswitchinterval() = 0.005
# [C++][00:41:12.663] Hello from the default_pool in release_gstate
# [Python][00:41:02.664] Hello from custom_pool, a = 1!
# [Python][00:41:12.664] a = 1 in release_gstate!
# [Python][00:41:12.664] thread_local.name = default_pool in release_gstate!
# [Python][00:41:12.664] sys.getswitchinterval() = 0.005
# [C++][00:41:12.664] Hello from the custom_pool in release_gstate
# [Python][00:41:12.664] a = 1 in release_gstate!
# [Python][00:41:12.664] thread_local.name = custom_pool in release_gstate!
```

## Example 6

* 沒有在 main function 中傳入 PyGILState_STATE 到 `init_python_thread`，而是在 `init_python_thread` 中呼叫 `PyGILState_Ensure` 來取得，並且將 `PyGILState_STATE` 傳遞給 callback function，之後再使用 `PyGILState_Release` 來釋放。
* [PyGILState_STATE](https://github.com/python/cpython/blob/75f38af7810af1c3ca567d6224a975f85aef970f/Include/pystate.h#L76-L78) 只是一個 enum，不是 PyObject，所以不會被 Python interpreter 管理。


is merely an enum. It is not a PyObject, so it is not managed by reference counting.

```sh
g++ example6.cc -I/usr/include/python3.9 -lpython3.9 -lpthread -o example6
./example6

# [C++][09:18:50.471] First post in default_pool
# [C++][09:18:50.472] First post in custom_pool
# [C++][09:18:50.472] Hello from the default_pool in init_python_thread
# [Python][09:18:50.472] Hello from default_pool!
# [C++][09:18:50.472] Second post in default_pool
# [C++] PyGILState_Release()
# [C++][09:18:50.472] Hello from the custom_pool in init_python_thread
# [Python][09:18:50.472] Hello from custom_pool!
# [C++][09:18:50.472] Second post in custom_pool
# [C++] PyGILState_Release()
```