#!/usr/bin/env bash
# 04 — Open files: CRIU saves the fd, path, flags and offset, but NOT the file
# contents. The file has to be there, unchanged, at restore time.
source "$(dirname "$0")/common.sh"
init 04_open_files
CLEANUP_PATTERNS=("python3 writer.py")

cat > writer.py <<'EOF'
import time
f = open("data.txt", "w")
i = 0
while True:
    i += 1
    f.write(f"line {i}\n"); f.flush()
    time.sleep(1)
EOF

setsid python3 writer.py > /dev/null 2>&1 < /dev/null &
PID=$(wait_pid "python3 writer.py")
sleep 3

step "The fd as the kernel sees it: path + current offset"
FD=$(ls -l /proc/$PID/fd | awk '/data.txt/ {print $9}')
run "grep pos /proc/$PID/fdinfo/$FD"

step "Case A: dump, leave the file alone, restore -> writing resumes at the same offset"
mkdir a
run "criu dump -t $PID -D a -o dump.log"
run "criu restore -D a -d -o restore.log"
sleep 2
run "cat data.txt"
note "no gap and no overwrite: the offset came back with the fd"
kill "$PID"; sleep 0.5

step "Case B: dump, then change the file before restore"
setsid python3 writer.py > /dev/null 2>&1 < /dev/null &
PID=$(wait_pid "python3 writer.py")
sleep 2
mkdir b
run "criu dump -t $PID -D b -o dump.log"
run "echo 'someone else wrote this' >> data.txt"
run "criu restore -D b -d -o restore.log || echo '>>> restore FAILED (expected)'"
run "grep -m1 -i 'size' b/restore.log"
note "CRIU checks the size of every regular file it reopens; a changed file means the"
note "process's view of the world no longer matches, so it refuses to restore."
note "In containers this is why the root fs must be the same image (or a snapshot of it)."
