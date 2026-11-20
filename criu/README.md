# CRIU

CRIU（Checkpoint/Restore In Userspace）可以把一個正在跑的 Linux process tree「凍結」成一堆檔案（images），
之後再從這些檔案把 process 原封不動地叫回來：同一個 PID、同樣的記憶體、同樣開著的檔案與 socket，
程式本身完全不知道自己被暫停過。

* 只能在 Linux 上跑（依賴 ptrace、`/proc`、namespaces、`CONFIG_CHECKPOINT_RESTORE`），Mac 要開 Linux VM。
* 需要 root / `CAP_SYS_ADMIN`（或 `CAP_CHECKPOINT_RESTORE`），在容器裡通常要 privileged 且關掉 seccomp。

## 最基本的 dump / restore

```bash
bash basic.sh

# [Expected Output]
# $ criu dump -t 4305 -D img -o dump.log
# pid 4305 is gone
# $ du -sh img
# 3.0M	img
# last line 3s ago : [pid 4305] count=4
# last line now    : [pid 4305] count=4          <- 凍在硬碟上時什麼都不會發生
# $ criu restore -D img -d -o restore.log
# [pid 4305] count=5
# [pid 4305] count=6
# restored with the SAME pid 4305
```

* `criu dump -t <pid> -D <dir>`：凍結 process tree，把狀態寫進 `<dir>`，成功後**預設會殺掉原本的 process**。
* `criu restore -D <dir> -d`：從 images 重建 process。`-d` 讓 criu 自己退出、restored process 留在背景跑。
* Restore 會用**同一個 PID**，所以那個 PID 必須是空的。
  * 如果原本的 process 變成 zombie 沒被回收，restore 會失敗：`Can't fork for <pid>: File exists`。
  * 容器的 PID 1 若是 `sleep infinity` 這類不會回收 zombie 的程式，就容易遇到；PID 1 改用 `tini` 之類的 init 可以避免。
* 用 `setsid` 啟動是為了脫離目前 shell 的 session / terminal；若 process 綁在 terminal 上，dump 和 restore 都要加 `--shell-job`。
* `img/` 裡：`core-<pid>.img`（CPU 暫存器、signal 等）、`mm-` / `pagemap-` / `pages-`（記憶體）、`files.img` / `fdinfo-`（fd）、`pstree.img`（process tree）。

## GPU process：cuda-checkpoint + CRIU，並換到另一張 GPU

```bash
bash cuda_checkpoint.sh

# [Expected Output]
# gpu counter=2  (running on PCI 0000:0F:00.0)
# 5304, 00000000:0F:00.0, 418 MiB
# $ cuda-checkpoint --action lock --pid 5304          -> locked
# $ cuda-checkpoint --action checkpoint --pid 5304    -> checkpointed
# (nvidia-smi 上已經看不到這個 process)
# $ criu dump ...          451M img
# $ criu restore ...       -> 狀態仍是 checkpointed
# $ cuda-checkpoint --action restore --pid 5304 --device-map '<GPU0>=<GPU1>,<GPU1>=<GPU0>,<其他>=<自己>'
# $ cuda-checkpoint --action unlock --pid 5304        -> running
# gpu counter=3  (running on PCI 0000:0F:00.0)        <- counter 從 GPU 記憶體接著跑
# 5304, 00000000:15:00.0, 418 MiB                     <- 但實際上已經在另一張 GPU 上
```

* 需要 NVIDIA 的 `cuda-checkpoint`（driver >= 550）、`nvcc`，以及至少 2 張 GPU。
* Counter 存在 GPU 記憶體裡、只有 kernel 會改它，所以 restore 後能接著數，就代表 GPU 狀態真的被保存了。
* CRIU 本身不懂 GPU。`cuda-checkpoint` 先把 GPU 狀態搬回 host memory，讓 process 變成「純 CPU process」，CRIU 才能 dump。
* 四個 action：
  * `lock`：等正在跑的 CUDA work 結束，並擋住新的 CUDA API call。
  * `checkpoint`：把 device memory 複製到 host memory，釋放 GPU（`nvidia-smi` 上看不到它了）。
  * `restore`：把狀態放回 GPU；可以用 `--device-map` 換到別張卡。
  * `unlock`：讓 CUDA API call 繼續。
  * `--toggle` = `lock + checkpoint` 或 `restore + unlock` 一次做完。
* 順序：`lock → checkpoint → criu dump → criu restore → restore → unlock`。
* `--device-map` 用來在 restore 時換卡，見下面的說明。
* 換卡對 process 是透明的：它還是以為自己在 device 0，連印出來的 PCI bus id 都是舊的，但 `nvidia-smi` 顯示它已經在 `15:00.0`。
* Image 大小約等於 GPU 記憶體用量（這裡 418 MiB → 451M）。大模型動輒幾十 GB，dump/restore 的 I/O 會是主要成本。

### `--device-map`

`--device-map` 告訴 `cuda-checkpoint`：checkpoint 時用的是哪張 GPU，restore 後要放到哪張 GPU 上。

* 格式：用逗號分隔多組 `舊UUID=新UUID`。左邊是 checkpoint 時 process 看到的 GPU，右邊是 restore 後實際要用的 GPU。
* GPU 用 UUID 指定，可以用 `nvidia-smi --query-gpu=uuid --format=csv,noheader` 查。

範例裡的 `<GPU0>=<GPU1>,<GPU1>=<GPU0>,<其他>=<自己>`：

| 寫法 | 意思 |
|---|---|
| `<GPU0>=<GPU1>` | 原本在 GPU 0 上的東西，搬到 GPU 1 |
| `<GPU1>=<GPU0>` | 原本在 GPU 1 上的東西，搬到 GPU 0 |
| `<其他>=<自己>` | GPU 2 到 7 不動，各自對應到自己 |

實際指令會換成真的 UUID，例如 `GPU-6d638d2f-...=GPU-afa48f98-...`，所以很長。

為什麼要讓 GPU 0 和 GPU 1 對調，而不是只寫 `<GPU0>=<GPU1>`：

* 這個 process 只用了 GPU 0，但它的 CUDA 環境看得到全部 8 張卡（沒有設 `CUDA_VISIBLE_DEVICES`）。
* 對應要一對一：每張舊卡對到一張新卡，不能兩張舊卡對到同一張新卡。只寫 GPU 0 → GPU 1 的話，原本的 GPU 1 就沒有地方可以對，最簡單的一對一寫法就是 0 和 1 互換。
* 所以範例把其他 6 張也寫進去，各自對到自己，讓對應表完整。（沒有測試過只寫部分 GPU 時 `cuda-checkpoint` 會怎麼處理。）

Restore 後 process 看到什麼：

* 換卡對 process 是透明的。它的 CUDA device 0 背後其實已經是實體的 GPU 1，但它還是叫它 device 0。
* 連 `cudaDeviceGetPCIBusId` 回傳的都還是舊的 `0F:00.0`；只有從外面用 `nvidia-smi` 看，才會發現它實際跑在 `15:00.0`。

實際用途：

* 搬到另一台機器：不同節點的 GPU UUID 都不一樣，restore 時要把舊節點的每張卡對到新節點的卡，否則 CUDA 找不到原本的 GPU。
* 同一台機器換卡：例如原本那張卡要維修，或要把工作集中到某幾張卡上，騰出整張卡給別人用。

## 重點整理

| CRIU 存什麼 | CRIU 不存什麼 |
|---|---|
| 記憶體（所有 page） | 檔案內容（只存路徑 + offset，restore 時要一致） |
| CPU 暫存器、signal、credentials | 外部的連線另一端（server 要自己還在） |
| fd、pipe、unix/TCP socket（加 flag） | GPU 狀態（要靠 cuda-checkpoint） |
| process tree、PID、namespaces | 硬體裝置的狀態（一般而言） |

* 適用場景：live migration、快速啟動（把暖機完的 process 存起來，之後直接 restore）、長時間 job 的容錯、debug（保存問題現場）。
