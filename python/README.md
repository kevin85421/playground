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

## Python dump heap

* https://blog.jjyao.me/blog/2024/09/13/python-heap-dump/
* https://github.com/zhuyifei1999/guppy3?tab=readme-ov-file

```sh
python3 -c "import time; l=[]; [print(i) or l.append(i) or time.sleep(1) for i in range(1000)]"

# Get PID
ps aux | grep "range(1000)"

# Attach to PID
pyrasite-shell $PID

# Dump heap
>>> from guppy import hpy; h=hpy(); h.heap()
Partition of a set of 51514 objects. Total size = 6100043 bytes.
 Index  Count   %     Size   % Cumulative  % Kind (class / dict of class)
     0  15356  30  1413167  23   1413167  23 str
     1  10339  20   723872  12   2137039  35 tuple
     2   3514   7   620746  10   2757785  45 types.CodeType
     3    683   1   587376  10   3345161  55 type
     4   6853  13   500138   8   3845299  63 bytes
     5   3246   6   441456   7   4286755  70 function
     6    683   1   334528   5   4621283  76 dict of type
     7    144   0   254328   4   4875611  80 dict of module
     8    456   1   198880   3   5074491  83 dict (no owner)
     9    106   0   113008   2   5187499  85 set
<183 more rows. Type e.g. '_.more' to view.>
```

## `@abstractmethod` / `@staticmethod` 的順序

```bash
python3 annotation_order.py
# Traceback (most recent call last):
#   File "/home/ubuntu/playground/python/annotation_order.py", line 15, in <module>
#     impl = Impl()
# TypeError: Can't instantiate abstract class Impl with abstract method get_communicator_metadata
```
* 因為 `class Impl(Base)` 沒有實作 `get_communicator_metadata`，因此會報錯。
* 為何先執行 `@abstractmethod` 再執行 `@staticmethod`？
  ```python
  class Base(ABC):

      @staticmethod
      @abstractmethod
      def get_communicator_metadata():
          pass
  ```
  * 會先執行 `@abstractmethod` 再執行 `@staticmethod`。
  * 如果交換順序後，由於 `@staticmethod` 設定後 `__isabstractmethod__` 變成不可 writable，[@abstractmethod](https://github.com/python/cpython/blob/8e3244d39b8cd3d7cef5a315247d45e801b35869/Lib/abc.py#L24) 會設定 `__isabstractmethod__`，因此會報錯。

## `attrs.define`

* 類似 dataclass，自動產生 `__init__`、`__repr__`、`__eq__` 等方法
* 使用 `@attrs.define` 裝飾器可以讓類別自動獲得這些常用方法
* `attrs` 比 `dataclass` 支持更多功能 ([ref](https://www.revsys.com/tidbits/dataclasses-and-attrs-when-and-why/))

```bash
python3 attrs_define.py
# [Example output]:
# Print a `Person` instance which is annotated by `attrs.define`
# Person(name='Alice', age=30, email='alice@example.com')
# Print a `Person2` instance which is not annotated by `attrs.define`
# <__main__.Person2 object at 0x102b6fca0>
```

## `hashable`

* https://docs.python.org/3/glossary.html#term-hashable
* 定義：An object is `hashable` if it has a hash value which never changes during its lifetime (it needs a `__hash__()` method), and can be compared to other objects (it needs an `__eq__()` method). Hashable objects which compare equal must have the same hash value.
  * 一個 `hashable` object 可以作為 dict 的 key 或者 set 的 member。
  * 多數 Python immutable built-in objects 為 hashable。如果是用戶定義的 class instances 預設也是 hashable，會透過比較 `id()`。

```bash
python3 hashable.py
# [Example output]
# Person('Alice', 20) in d:  False
# Person2('Alice', 20) in d2:  False
# Person3('Alice', 20) in d3:  True
```
* `Person`：`__hash__` 和 `__eq__` 都沒有實作。
* `Person2`：實作 `__hash__` 但沒有 `__eq__`。
* `Person3`：實作 `__hash__` 和 `__eq__`。

## `set.update(...)` 不會改變其中 instances 如果該 member 已存在

```python
# python3 hashable.py
alice1 = Person3("Alice", 20)
id1 = id(alice1)
alice2 = Person3("Alice", 20)
id2 = id(alice2)
s = set([alice1])
assert alice2 in s
s.update([alice2])

l = list(s)
assert len(l) == 1
assert l[0] is alice1
assert l[0] is not alice2
```

## `os.O_DIRECT`

```bash
python3 os_direct_example.py
# [Example output]
# Logical block size: 4096
# Read 8192 bytes: b'Hello, World!Hello, '
```
* 只能在 Linux 上運行，Mac 上好像沒有 `O_DIRECT`。
* [O_DIRECT](https://man7.org/linux/man-pages/man2/open.2.html)：
  * 使用 `O_DIRECT` 開啟時，會直接與儲存設備交互，繞過 Linux 內核的頁面 cache。
  * 通常會降低性能，但在特別情況可能有用。
  * Linus 強烈反對 `O_DIRECT`：https://lkml.org/lkml/2007/1/10/233
  
* 記得閱讀 [open(2)](https://man7.org/linux/man-pages/man2/open.2.html) 下方 "The O_DIRECT flag may impose alignment restrictions on the length" 的說明。
  * "Likewise, applications should avoid mixing mmap(2) of files with direct I/O to the same files."
    * 此 example 不是使用 `mmap` 來將 file 映射到 memory，而是使用 `mmap` 建立 buffer 來符合 alignment 需求。
  * "In summary, `O_DIRECT` is a potentially powerful tool that should be used with caution.  It is recommended that applications treat use of O_DIRECT as a performance option which is disabled by default."

* 將 `buffer_size = block_size * 2  # 例如 8192 位元組` 改成 `buffer_size = block_size * 2 + 1`。沒符合 alignment，因此丟出 `EINVAL`。
  ```
  [Errno 22] Invalid argument
  ```

## `try ... except ... else`

```bash
python3 try_except_else.py

# [expected output]
# Case 1: No exception raised in `try`
# try
# else
# Case 2: Exception raised in `try`
# except
```

* `else` 只有在 `try` 之中沒有丟出 exception 時被執行。

## Process Group

* Experiment 1: 沒設定 process group，然後使用 `os.kill` 發送 SIGKILL 給 leader process
  ```sh
  uv run process_group.py --sleep-before-kill 5 --no-use-process-group --no-use-kill-pg

  # [example output]:
  #
  # [monitor] args: Namespace(sleep_before_kill=5.0, use_process_group=False, use_kill_pg=False)
  # [monitor] starting leader in a NEW SESSION/PROCESS GROUP... (sleep_before_kill: 5.0, use_process_group: False)
  # [monitor] leader pid=41906
  # [monitor] sleeping for 5.0 seconds to wait for the child process to start...
  # [leader] pid=41906 pgid=41904
  # [child] pid=41907 ppid=41906 pgid=41904
  # [monitor] sending SIGKILL to leader only...
  # [monitor] done.

  # 檢查 child process，發現 child process 仍存在
  ps aux | grep 41907
  # kai-hsun         41907   0.0  0.0 411022896  11872 s024  S     4:30PM   0:00.01 ...
  kill 41907
  # [child] got signal 15, exiting...
  ```
  * 先啟動一個 leader / child process，其中 leader 是 child 的 parent process，但沒設定 process group。
  * 發送 SIGKILL 給 leader `os.kill(leader.pid, signal.SIGKILL)`。

* Experiment 2: 設定 process group，然後使用 `os.kill` 發送 SIGKILL 給 leader process
  ```sh
  uv run process_group.py --sleep-before-kill 5 --use-process-group --no-use-kill-pg

  # [example output]
  #
  # [monitor] args: Namespace(sleep_before_kill=5.0, use_process_group=True, use_kill_pg=False)
  # [monitor] starting leader in a NEW SESSION/PROCESS GROUP... (sleep_before_kill: 5.0, use_process_group: True)
  # [monitor] leader pid=66024
  # [monitor] sleeping for 5.0 seconds to wait for the child process to start...
  # [leader] pid=66024 pgid=66024
  # [child] pid=66035 ppid=66024 pgid=66024
  # [monitor] sending SIGKILL to leader only...
  # [monitor] done.

  ps aux | grep 66035
  # kai-hsun         66035   0.0  0.0 411034160  12096   ??  S     4:33PM   0:00.01 ...

  kill 66035
  # [child] got signal 15, exiting...
  ```

* Experiment 3: 設定 process group，然後使用 `os.killpg` 發送 SIGKILL 給 process group
  ```sh
  uv run process_group.py --sleep-before-kill 5 --use-process-group --use-kill-pg

  # [example output]
  #
  # [monitor] args: Namespace(sleep_before_kill=5.0, use_process_group=True, use_kill_pg=True)
  # [monitor] starting leader in a NEW SESSION/PROCESS GROUP... (sleep_before_kill: 5.0, use_process_group: True)
  # [monitor] leader pid=82754
  # [monitor] sleeping for 5.0 seconds to wait for the child process to start...
  # [leader] pid=82754 pgid=82754
  # [child] pid=82755 ppid=82754 pgid=82754
  # [monitor] cleaning up its process group...
  # [monitor] sending SIGTERM to process group 82754...
  # [child] got signal 15, exiting...
  # [monitor] done.

  ps aux | grep 82755
  # => note that the signal handler of child has already been executed "[child] got signal 15, exiting...".
  ```

## `subprocess.Popen.poll()`

```bash
python3 subprocess_poll.py
# [Example output]
# Process is still running... Mon Oct 14 09:06:15 2025
# Process is still running... Mon Oct 14 09:06:16 2025
# Process is still running... Mon Oct 14 09:06:17 2025
```
* https://docs.python.org/3/library/subprocess.html#subprocess.Popen.poll
* 如果 process 還在運行，`poll()` 回傳 `None`。