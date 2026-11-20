#!/usr/bin/env bash
# 01 — The smallest dump/restore: freeze a process to disk, kill it, bring it back.
source "$(dirname "$0")/common.sh"
init 01_basic
CLEANUP_PATTERNS=("python3 counter.py")

cat > counter.py <<'EOF'
import os, time
i = 0
while True:
    i += 1
    print(f"[pid {os.getpid()}] count={i}", flush=True)
    time.sleep(1)
EOF

step "Start a counter that prints once per second"
note "setsid: detach from this shell's session/terminal, otherwise dump and restore both need --shell-job"
setsid python3 counter.py > out.log 2>&1 < /dev/null &
PID=$(wait_pid "python3 counter.py")
sleep 3
run "tail -n 2 out.log"

step "criu dump: freeze the process tree and write its state into ./img"
note "dump kills the process after a successful dump (unless you pass --leave-running)"
mkdir img
run "criu dump -t $PID -D img -o dump.log"
alive "$PID" && echo "still alive?" || echo "pid $PID is gone"
run "ls img | head -20"
run "du -sh img"

step "Nothing happens while it is on disk"
BEFORE=$(tail -n 1 out.log); sleep 3; AFTER=$(tail -n 1 out.log)
echo "last line 3s ago : $BEFORE"
echo "last line now    : $AFTER"

step "criu restore: rebuild the process from ./img"
note "-d: detach, so criu returns and the restored process keeps running in the background"
run "criu restore -D img -d -o restore.log"
sleep 3
run "tail -n 4 out.log"
alive "$PID" && echo "restored with the SAME pid $PID (CRIU needs that PID to be free)"
