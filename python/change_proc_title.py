from setproctitle import setproctitle
import time

# 設定新的進程標題
setproctitle("my_python_process")

print("Process title changed to 'my_python_process'.")
# 持續運行程式，以便你可以使用 ps 等工具觀察進程標題的變化
while True:
    time.sleep(5)
