# CRIU

CRIU（Checkpoint/Restore In Userspace）可以把一個正在跑的 Linux process tree「凍結」成一堆檔案（images），
之後再從這些檔案把 process 原封不動地叫回來：同一個 PID、同樣的記憶體、同樣開著的檔案與 socket，
程式本身完全不知道自己被暫停過。

* 只能在 Linux 上跑（依賴 ptrace、`/proc`、namespaces、`CONFIG_CHECKPOINT_RESTORE`），Mac 要開 Linux VM。
* 需要 root / `CAP_SYS_ADMIN`（或 `CAP_CHECKPOINT_RESTORE`），在容器裡通常要 privileged 且關掉 seccomp。
* GPU process 要搭配 NVIDIA 的 `cuda-checkpoint`（driver >= 550）先把 GPU 狀態搬回 host memory。

## 環境

以下範例都在 oke-ashburn-gpu 的 `kaihsun-criu-test` Pod（Ubuntu 24.04、privileged、8×A100、driver 580）實際跑過，
`[Expected Output]` 都是真實輸出（PID、port 每次會不同）。

```bash
# 安裝（在 Pod 裡）
add-apt-repository -y ppa:criu/ppa && apt-get install -y criu        # criu 4.3，附 crit
curl -fsSL -o /usr/local/bin/cuda-checkpoint \
  https://github.com/NVIDIA/cuda-checkpoint/raw/main/bin/x86_64_Linux/cuda-checkpoint
chmod +x /usr/local/bin/cuda-checkpoint
criu check                                                           # Looks good.

# 把範例丟進 Pod
kubectl --context oke-ashburn-gpu cp . default/kaihsun-criu-test:/root/criu-examples
kubectl --context oke-ashburn-gpu -n default exec -it kaihsun-criu-test -- bash /root/criu-examples/01_basic.sh
```

每個範例都在 `/tmp/criu-examples/<name>/` 底下工作，跑完會自動清掉自己啟動的 process，可以重複執行。

## 01 — 最基本的 dump / restore

```bash
bash 01_basic.sh

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
* Restore 會用**同一個 PID**，所以那個 PID 必須是空的（見下面的「PID 1 與 zombie」）。
* 用 `setsid` 啟動是為了脫離目前 shell 的 session / terminal；若 process 綁在 terminal 上，dump 和 restore 都要加 `--shell-job`。
* `img/` 裡：`core-<pid>.img`（CPU 暫存器、signal 等）、`mm-` / `pagemap-` / `pages-`（記憶體）、`files.img` / `fdinfo-`（fd）、`pstree.img`（process tree）。

## 02 — Snapshot 與「時光倒流」

```bash
bash 02_snapshot_rewind.sh

# [Expected Output]
# $ criu dump -t 4620 -D snap -o dump.log --leave-running
# snapshot taken at: count=4
# now at: count=9
# >>> restore FAILED (expected)
# Error (criu/files-reg.c:2175): File .../out.log has bad size 72 (expect 32)
# $ cp snap/out.log.saved out.log
# $ criu restore -D snap -d -o restore.log
# count=1 ... count=4, count=5, count=6        <- 從 snapshot 的 count=4 繼續
```

* `--leave-running`：dump 完不殺 process，等於拍一張 snapshot。之後 restore 就是把 process「倒帶」回拍照當下。
* 第一次 restore 失敗是重點：**CRIU 只存 fd、路徑和 offset，不存檔案內容**，而且 restore 時會檢查檔案大小。
  process 拍照後 `out.log` 又長大了，CRIU 就拒絕 restore。
* 所以 snapshot 必須「process + 它看到的檔案系統」一起拍。容器的 checkpoint（Podman / CRI-O）就是這樣做的：
  rootfs 的變更也會一起打包。

## 03 — 整棵 process tree（parent + child + pipe）

```bash
bash 03_process_tree.sh

# [Expected Output]
#    PID    PPID CMD
#   4728    4720 python3 family.py
#   4735    4728 python3 family.py
# $ criu dump -t 4728 -D img -o dump.log
# both processes are gone
# core-4728.img  core-4735.img  pipes-data.img  pstree.img
# $ criu restore -D img -d -o restore.log
#   4728    4711 python3 family.py               <- 兩個都回來了，PID 不變
#   4735    4728 python3 family.py
# [parent 4728] got 7 from child                 <- 還是透過同一個 pipe 溝通
```

* `-t` 給的是 tree 的 root，底下所有 child 會一起 dump。
* Pipe 這種「兩端都在 tree 裡」的資源 CRIU 可以完整重建，包括還在 pipe buffer 裡沒被讀走的資料（`pipes-data.img`）。
* Restore 後 root 的 PPID 會變（變成執行 restore 的那個 process 或 subreaper），因為原本的 parent 不在 tree 裡。

## 04 — 開著的檔案

```bash
bash 04_open_files.sh

# [Expected Output]
# $ grep pos /proc/4805/fdinfo/3
# pos:	28
# Case A: dump -> restore，檔案沒動
# line 1 ... line 6                              <- 沒有空洞、沒有覆寫，offset 跟著 fd 回來了
# Case B: dump -> 改檔案 -> restore
# >>> restore FAILED (expected)
# Error (criu/files-reg.c:2175): File .../data.txt has bad size 45 (expect 21)
```

* 對 regular file，CRIU 存的是：路徑、open flags、offset。Restore 時重新 open 並 seek 回去。
* Restore 時檔案必須存在且大小一致，否則失敗。這是 CRIU 保護你：process 記憶體裡對檔案的認知已經和現實不一致了。
* 搬到另一台機器 restore 時，檔案系統也要一樣（同一個 container image，或共享儲存）。

## 05 — TCP 連線不斷線

```bash
bash 05_tcp.sh

# [Expected Output]
# client (local port 57140): sent ping 3, got pong 3
# Error (criu/sk-inet.c:201): inet: Connected TCP socket, consider using --tcp-established option.
# $ criu dump -t 4940 -D img -o dump.log --tcp-established --network-lock nftables
# $ criu restore -D img -d -o restore.log --tcp-established --network-lock nftables
# client (local port 57140): sent ping 4, got pong 4   <- 同一個 local port，同一條連線
```

* 預設 CRIU 不 dump 已建立的 TCP 連線，要明確加 `--tcp-established`。
* 原理是 kernel 的 `TCP_REPAIR` 模式：把 sequence number、window、send/recv queue 裡的資料都讀出來，restore 時再塞回去。
* `--network-lock`：凍結期間要擋住這條連線的封包，否則對方送來的封包會被 kernel 回 RST 把連線打斷。
  這個 Pod 沒裝 iptables，所以用 `nftables`。
* Server 端完全不知道 client 被凍結過，只是覺得對方安靜了幾秒。
* 跨機器搬移時，IP 也要跟著搬（同一個 Pod IP / VIP），否則 TCP 4-tuple 對不上。

## 06 — Pre-dump：讓凍結時間變短（live migration 的原理）

```bash
bash 06_pre_dump.sh

# [Expected Output]
# plain dump  : frozen 400 ms, pages written 262912 (1027 MiB)
# pre-dump #1 : frozen 43 ms, pages written 262912 (1027 MiB)
# pre-dump #2 : frozen 16 ms, pages written 12528 (48 MiB)
# final dump  : frozen 137 ms, pages written 10480 (40 MiB)
# 1.1G full   1.1G pre1   49M pre2   41M final
```

* 一般 dump 要在 process **停住的狀態下**把全部記憶體寫出去，記憶體越大停越久（1 GiB 就 400 ms）。
* `criu pre-dump --track-mem`：只短暫停一下收集 page 清單，然後**邊跑邊複製**記憶體，並開啟 kernel 的 soft-dirty tracking。
* 下一輪 `--prev-images-dir ../pre1` 只寫出上次之後被改過的 page（這裡 1 GiB 中只有 48 MiB 變了）。
* 最後的 `dump` 只需要寫最後一點點差異，停機時間從 400 ms 降到 137 ms。
* Images 是一條鏈（`final -> pre2 -> pre1`），restore 時會沿著鏈把記憶體拼回來。
* 記憶體改得越快，pre-dump 越收斂不了；這也是 live migration 的極限。

## 07 — 用 crit 看 images 裡有什麼

```bash
bash 07_crit.sh

# [Expected Output]
# $ crit x img ps
#     PID   PGID    SID   COMM
#    5224   5224   5224   python3
# $ crit x img fds
#   3: /tmp/criu-examples/07_crit/sample.log
#   4: pipe[2290175109]
# $ crit x img mems | head
#   00400000-00420000   r-- /usr/bin/python3.12
#   ...
# {'ip': '0x7de214e73a78', 'sp': '0x7fff1ccec3b0', 'ax': '0xe6'}   <- 凍結當下的 CPU 暫存器
# $ grep -c 'hello-from-the-heap' img/pages-*.img
# 3
```

* Images 是 protobuf 格式，`crit`（CRIU Image Tool）可以 decode 成 JSON：`crit show <file>`、`crit x <dir> ps|fds|mems|rss`。
* `pages-*.img` 就是原始的記憶體內容，可以直接 grep 到程式裡的字串。
  **Checkpoint images 等同 process 的完整記憶體 dump，裡面可能有 token、密碼、資料，要當成機密處理。**

## 08 — GPU process：cuda-checkpoint + CRIU，並換到另一張 GPU

```bash
bash 08_cuda.sh

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

* CRIU 本身不懂 GPU。`cuda-checkpoint` 先把 GPU 狀態搬回 host memory，讓 process 變成「純 CPU process」，CRIU 才能 dump。
* 四個 action：
  * `lock`：等正在跑的 CUDA work 結束，並擋住新的 CUDA API call。
  * `checkpoint`：把 device memory 複製到 host memory，釋放 GPU（`nvidia-smi` 上看不到它了）。
  * `restore`：把狀態放回 GPU；可以用 `--device-map` 換到別張卡。
  * `unlock`：讓 CUDA API call 繼續。
  * `--toggle` = `lock + checkpoint` 或 `restore + unlock` 一次做完。
* 順序：`lock → checkpoint → criu dump → criu restore → restore → unlock`。
* `--device-map` 必須涵蓋 process 看得到的**所有** GPU（所以其他卡 map 到自己）。
* 換卡對 process 是透明的：它還是以為自己在 device 0，連印出來的 PCI bus id 都是舊的，但 `nvidia-smi` 顯示它已經在 `15:00.0`。
* Image 大小約等於 GPU 記憶體用量（這裡 418 MiB → 451M）。大模型動輒幾十 GB，dump/restore 的 I/O 會是主要成本。

## PID 1 與 zombie（踩到的坑）

第一次跑 02 / 03 時 restore 失敗：

```
Error (criu/cr-restore.c:1245): Can't fork for 4448: File exists
```

* 這個 Pod 的 PID 1 是 `sleep infinity`，它**不會回收（reap）zombie**。
* 被 `criu restore -d` 交給 PID 1 的 process，或 parent 先死掉的 orphan，結束後會一直以 zombie 形式佔著 PID。
* CRIU 必須用原本的 PID restore，PID 被 zombie 佔住就失敗。
* 解法：
  * 容器的 PID 1 用會 reap 的 init，例如 `tini`、`dumb-init`，或 `docker run --init`。
  * 或像這裡的 [`reaper.py`](reaper.py)：用 `PR_SET_CHILD_SUBREAPER` 讓自己成為子樹的 subreaper，負責回收 orphan。
    `common.sh` 會自動用它包住每個範例。
* 實際在 K8s 做 checkpoint/restore 時，restore 到新的 Pod（新的 PID namespace）就不會撞到 PID。

## 重點整理

| CRIU 存什麼 | CRIU 不存什麼 |
|---|---|
| 記憶體（所有 page） | 檔案內容（只存路徑 + offset，restore 時要一致） |
| CPU 暫存器、signal、credentials | 外部的連線另一端（server 要自己還在） |
| fd、pipe、unix/TCP socket（加 flag） | GPU 狀態（要靠 cuda-checkpoint） |
| process tree、PID、namespaces | 硬體裝置的狀態（一般而言） |

* 適用場景：live migration、快速啟動（把暖機完的 process 存起來，之後直接 restore）、長時間 job 的容錯、debug（保存問題現場）。
* 和 ModelExpress 的關係：ModelExpress 的 `pause_serving` / `resume_serving` 讓推論 worker 能安全地經歷
  「`cuda-checkpoint` + CRIU」這個流程（暫停 P2P 分享、釋放 NIXL 鎖住的 GPU 記憶體，restore 後再重新註冊）。
