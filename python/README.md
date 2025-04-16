## setproctitle

* `/proc/<pid>/comm`: process 名稱
* `/proc/<pid>/cmdline`: process 的完整命令行 (通常 process 名稱會是第一個參數)

```bash
python3 change_proc_title.py

ps aux | grep my_python_process
# [Example output]:
# ubuntu    512413  0.0  0.0  16156  9816 pts/13   S+   20:01   0:00 my_python_process

cat /proc/512413/comm
# [Example output]: 
# 在 Linux 系統中，/proc/<pid>/comm 的內容一般限制在 16 個字元（包含結束的 NULL 字元）
# 因此實際可用的長度通常會更短。這個限制意味著如果設定的名稱超過這個長度，可能會被截斷或無法完整顯示。
# my_python_proce
```

## subprocess.Popen.wait()

* 如果沒有呼叫 `wait()` 的話，process 會變成 zombie process。

```bash
python3 subprocess_wait.py
# [Example output]:
# pid: 2553978 exists: True

# uncomment `process.wait()`
# [Example output]:
# pid: 2554148 exists: False
```

## 存取 Python class 的屬性

* 首先會先檢查 `__dict__` 中是否存在該屬性。
* 如果沒有，則會呼叫 `__getattr__`。
* 如果 `__getattr__` 也沒有，則會拋出 `AttributeError`。

此例子中，在 `__del__` 中存取已經被移除 `__dict__` 的屬性 `hello`，因此
呼叫 `__getattr__` 時，但是 `__getattr__` 存取 `world` 時，但是 `world` 也
不存在於 `__dict__` 中，因此又呼叫 `__getattr__`，如此不停 recursive。

```bash
python3 access_non_exist_attr.py

# hello world
# {'hello': 'hello', 'world': 'world'}
# Call __del__
# Exception ignored in: <function MyClass.__del__ at 0x7ff48b34a680>
# Traceback (most recent call last):
#   File "access_non_exist_attr.py", line 8, in __del__
#     self.hello
#   File "access_non_exist_attr.py", line 11, in __getattr__
#     if self.world == "world":
#   File "access_non_exist_attr.py", line 11, in __getattr__
#     if self.world == "world":
#   File "access_non_exist_attr.py", line 11, in __getattr__
#     if self.world == "world":
#   [Previous line repeated 496 more times]
# RecursionError: maximum recursion depth exceeded while calling a Python object
```

## `getattr` / `__getattr__` / `__getattribute__` 比較

```bash
python3 access_attr.py

# Case 1: e.existing which is exist in __dict__
# __getattribute__ called with: existing
# I exist
# --------------------------------------------------
# Case 2: e.dynamic which is not exist in __dict__, but can be handled by __getattr__
# __getattribute__ called with: dynamic
# __getattr__ called with: dynamic
# I am dynamic!
# --------------------------------------------------
# Case 3: getattr existing attribute
# __getattribute__ called with: existing
# I exist
# --------------------------------------------------
# Case 4: getattr non-existent attribute
# __getattribute__ called with: non_existent
# __getattr__ called with: non_existent
# __getattribute__ called with: __class__
# default value
```

* `getattr` 會先呼叫 `__getattribute__`，如果 `__getattribute__` 找不到，
  則會呼叫 `__getattr__`。
* `__getattribute__` 會直接存取屬性，不會去呼叫 `__getattr__`。
* `__getattr__` 只有在 `__getattribute__` 找不到屬性時，才會被呼叫。

