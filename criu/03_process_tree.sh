#!/usr/bin/env bash
# 03 — CRIU dumps a whole process TREE: a parent, its child, and the pipe between them.
source "$(dirname "$0")/common.sh"
init 03_process_tree
CLEANUP_PATTERNS=("python3 family.py")

cat > family.py <<'EOF'
import os, time
r, w = os.pipe()
if os.fork() == 0:                      # child: produce numbers into the pipe
    os.close(r)
    n = 0
    while True:
        n += 1
        os.write(w, f"{n}\n".encode())
        time.sleep(1)
os.close(w)                             # parent: consume them
with os.fdopen(r) as pipe:
    for line in pipe:
        print(f"[parent {os.getpid()}] got {line.strip()} from child", flush=True)
EOF

setsid python3 family.py > out.log 2>&1 < /dev/null &
PARENT=$(wait_pid "python3 family.py")
sleep 3
run "ps -o pid,ppid,cmd --ppid $PARENT -p $PARENT"

step "Dump by the parent PID: -t takes the root of the tree, children come along"
mkdir img
run "criu dump -t $PARENT -D img -o dump.log"
run "pgrep -f 'python3 family.py' || echo 'both processes are gone'"

step "Look at what was saved"
note "one core-<pid>.img per process, pstree.img holds the tree, pipes-data.img the bytes in flight"
run "ls img | grep -E 'core-|pstree|pipes'"

step "Restore: both processes come back, still connected by the same pipe"
run "criu restore -D img -d -o restore.log"
sleep 3
run "ps -o pid,ppid,cmd --ppid $PARENT -p $PARENT"
run "tail -n 3 out.log"
