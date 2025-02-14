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

* 啟動兩個 Python threads，不需要等到其中一個 thread 呼叫 PyGILState_Release 才能執行另一個 thread。
* Python threads 在呼叫 PyGILState_Release 後，py-spy 就看不到該 Python threads。

```sh
g++ example3.cc -I/usr/include/python3.9 -lpython3.9 -lpthread -o example3
./example3
```
