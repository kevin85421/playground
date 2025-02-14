# Non-Python Created Threads

* https://docs.python.org/3/c-api/init.html#non-python-created-threads

```sh
g++ main.cc -I/usr/include/python3.8 -lpython3.8 -lpthread -o main
./main

# 使用 py-spy 查看，包含兩個 threads，由於 pthread_t cpp_thread 沒有執行 Python code，
# 因此不會被 Python interpreter 管理，所以不會出現在 py-spy 的結果中。
# (1) main thread
# (2) pthread_t py_thread;
sudo env "PATH=$PATH" py-spy dump -p 389596

# [Example output]
# Process 389596: ./main
# Python v3.8.10 (/home/ubuntu/workspace/playground/python/non_python_threads/main)

# Thread 389596 (idle)
# Thread 389597 (idle)
```
