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