from multiprocessing import Process
from multiprocessing import shared_memory
import numpy as np


def child_process(shm_name, size):
    # 連接到父進程的共享記憶體
    shm = shared_memory.SharedMemory(name=shm_name)
    arr = np.ndarray((size,), dtype=np.int64, buffer=shm.buf)

    print("[子進程] 原始值：", arr[:])
    arr[0] = 999  # 修改共享記憶體的內容
    print("[子進程] 修改後：", arr[:])

    shm.close()


if __name__ == "__main__":
    size = 10
    # 建立共享記憶體與 numpy 陣列
    shm = shared_memory.SharedMemory(create=True, size=size * 8)  # 每個 int64 是 8 bytes
    arr = np.ndarray((size,), dtype=np.int64, buffer=shm.buf)
    arr[:] = np.arange(size)  # 初始化

    print("[父進程] 初始陣列：", arr[:])

    # 建立子進程，並傳遞共享記憶體名稱
    p = Process(target=child_process, args=(shm.name, size))
    p.start()
    p.join()

    print("[父進程] 子進程後陣列：", arr[:])

    # 清理共享記憶體
    shm.close()
    shm.unlink()
