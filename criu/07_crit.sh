#!/usr/bin/env bash
# 07 — Look inside a checkpoint with crit (CRIU Image Tool).
# The images are protobuf files; crit decodes them to JSON.
source "$(dirname "$0")/common.sh"
init 07_crit
CLEANUP_PATTERNS=("python3 sample.py")

cat > sample.py <<'EOF'
import os, time
log = open("sample.log", "w")
secret = "hello-from-the-heap " * 1000
r, w = os.pipe()
while True:
    log.write("."); log.flush()
    time.sleep(1)
EOF

setsid python3 sample.py > /dev/null 2>&1 < /dev/null &
PID=$(wait_pid "python3 sample.py")
sleep 2
mkdir img
criu dump -t "$PID" -D img -o dump.log --leave-running
kill "$PID"

step "crit x ps: the process tree"
run "crit x img ps"

step "crit x fds: every open fd and what it points to"
run "crit x img fds"

step "crit x mems: the memory map (like /proc/PID/maps)"
run "crit x img mems | head -25"

step "crit show: raw decode of one image, e.g. the CPU registers in core-$PID.img"
run "crit show img/core-$PID.img | python3 -c 'import json,sys; t=json.load(sys.stdin)[\"entries\"][0][\"thread_info\"][\"gpregs\"]; print({k: t[k] for k in (\"ip\",\"sp\",\"ax\")})'"

step "The memory itself is in pages-*.img, raw. Our string is in there:"
run "grep -c 'hello-from-the-heap' img/pages-*.img"
note "so a checkpoint contains everything in memory: keys, tokens, data. Treat images as secrets."
