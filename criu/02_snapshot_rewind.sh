#!/usr/bin/env bash
# 02 — --leave-running turns a dump into a snapshot: the process keeps going,
# and restoring later "rewinds" it to the moment of the snapshot.
source "$(dirname "$0")/common.sh"
init 02_snapshot_rewind
CLEANUP_PATTERNS=("python3 counter.py")

cat > counter.py <<'EOF'
import os, time
i = 0
while True:
    i += 1
    print(f"count={i}", flush=True)
    time.sleep(1)
EOF

setsid python3 counter.py > out.log 2>&1 < /dev/null &
PID=$(wait_pid "python3 counter.py")
sleep 3

step "Take a snapshot without stopping the process"
mkdir snap
run "criu dump -t $PID -D snap -o dump.log --leave-running"
echo "snapshot taken at: $(tail -n 1 out.log)"
note "the process has out.log open; CRIU will insist it has the same size at restore,"
note "so snapshot the file together with the process (a container checkpoint does the"
note "same for its root filesystem)"
run "cp out.log snap/out.log.saved"
alive "$PID" && echo "pid $PID is still running"

step "Let it run on for a while"
sleep 5
echo "now at: $(tail -n 1 out.log)"

step "Kill it and try to restore the snapshot as-is"
kill "$PID"; sleep 0.5
run "criu restore -D snap -d -o restore.log || echo '>>> restore FAILED (expected)'"
run "grep -m1 'bad size' snap/restore.log"
note "out.log grew after the snapshot. CRIU saves fds and offsets, never file contents."

step "Put the file back the way it was at snapshot time, then restore"
run "cp snap/out.log.saved out.log"
run "criu restore -D snap -d -o restore.log"
sleep 2.5
run "cat out.log"
note "count=5..9 never happened as far as the restored process knows: it rewound to count=4"
