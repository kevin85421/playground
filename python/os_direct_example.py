import os
import mmap

# 檔案路徑
filename = "test_file.bin"

# 創建一個測試檔案（至少 1MB，確保有足夠數據）
with open(filename, "wb") as f:
    f.write(b"Hello, World!" * 100000)  # 約 1.2MB

# 取得檔案系統的邏輯區塊大小
stat = os.stat(filename)
block_size = stat.st_blksize  # 通常是 4096
print(f"Logical block size: {block_size}")

# 以 O_DIRECT 模式開啟檔案
fd = os.open(filename, os.O_RDONLY | os.O_DIRECT)
try:
    # 分配對齊的緩衝區使用 mmap
    buffer_size = block_size * 2  # 例如 8192 位元組
    with mmap.mmap(-1, buffer_size, flags=mmap.MAP_PRIVATE, prot=mmap.PROT_READ | mmap.PROT_WRITE) as mm:
        mv = memoryview(mm)

        # 確保 offset 對齊 block_size
        offset = 0  # 必須是 block_size 的倍數

        # 使用 preadv 讀取
        try:
            bytes_read = os.preadv(fd, [mv], offset)
            print(f"Read {bytes_read} bytes: {mm[:20]}")  # 顯示前 20 位元組
        except OSError as e:
            print(f"Error reading with preadv: {e}")
        finally:
            # 顯式釋放 memoryview 以避免 BufferError => `mv` 會持有 mmap 的記憶體 pointer，稱為 "exported pointer"，
            # 在 mmap 嘗試關閉該 "exported pointer" 時，但是 `mv` 仍持有該 pointer，所以會拋出 BufferError。
            #
            # "BufferError: cannot close exported pointers exist"
            #
            # 因此需要顯式釋放 `mv`，以避免 BufferError。
            mv = None
finally:
    os.close(fd)

# 清理測試檔案
os.remove(filename)