import subprocess
import psutil
import time

process = subprocess.Popen(["true"])
pid = process.pid
time.sleep(1)

# 如果沒有 process.wait() 的話，process 會變成 zombie process。
# 因此 exists: True，如果有的話則會變成 False。
# process.wait()
print(f"pid: {pid} exists: {psutil.pid_exists(pid)}")
