# CRIU

CRIU（Checkpoint/Restore In Userspace）可以把一個正在跑的 Linux process tree「凍結」成一堆檔案（images），
之後再從這些檔案把 process 原封不動地叫回來：同一個 PID、同樣的記憶體、同樣開著的檔案與 socket，
程式本身完全不知道自己被暫停過。

* 只能在 Linux 上跑（依賴 ptrace、`/proc`、namespaces、`CONFIG_CHECKPOINT_RESTORE`），Mac 要開 Linux VM。
* 需要 root / `CAP_SYS_ADMIN`（或 `CAP_CHECKPOINT_RESTORE`），在容器裡通常要 privileged 且關掉 seccomp。

## 環境

以下範例在 oke-ashburn-gpu 的 `kaihsun-criu-test` Pod（Ubuntu 24.04、kernel 6.8、privileged）實際跑過，
`[Expected Output]` 是真實輸出（PID 每次會不同）。

```bash
# 安裝（在 Pod 裡）
add-apt-repository -y ppa:criu/ppa && apt-get install -y criu        # criu 4.3
criu check                                                           # Looks good.

# 把範例丟進 Pod 並執行
kubectl --context oke-ashburn-gpu cp . default/kaihsun-criu-test:/root/criu-examples
kubectl --context oke-ashburn-gpu -n default exec -it kaihsun-criu-test -- bash /root/criu-examples/01_basic.sh
```

範例在 `/tmp/criu-examples/01_basic/` 底下工作，跑完會自動清掉自己啟動的 process，可以重複執行。

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
* Restore 會用**同一個 PID**，所以那個 PID 必須是空的。
  * 如果原本的 process 變成 zombie 沒被回收，restore 會失敗：`Can't fork for <pid>: File exists`。
  * 容器的 PID 1 若是 `sleep infinity` 這類不會回收 zombie 的程式，就容易遇到；PID 1 改用 `tini` 之類的 init 可以避免。
* 用 `setsid` 啟動是為了脫離目前 shell 的 session / terminal；若 process 綁在 terminal 上，dump 和 restore 都要加 `--shell-job`。
* `img/` 裡：`core-<pid>.img`（CPU 暫存器、signal 等）、`mm-` / `pagemap-` / `pages-`（記憶體）、`files.img` / `fdinfo-`（fd）、`pstree.img`（process tree）。

## 重點整理

| CRIU 存什麼 | CRIU 不存什麼 |
|---|---|
| 記憶體（所有 page） | 檔案內容（只存路徑 + offset，restore 時要一致） |
| CPU 暫存器、signal、credentials | 外部的連線另一端（server 要自己還在） |
| fd、pipe、unix/TCP socket（加 flag） | GPU 狀態（要靠 cuda-checkpoint） |
| process tree、PID、namespaces | 硬體裝置的狀態（一般而言） |

* 適用場景：live migration、快速啟動（把暖機完的 process 存起來，之後直接 restore）、長時間 job 的容錯、debug（保存問題現場）。
