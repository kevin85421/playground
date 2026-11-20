#!/usr/bin/env bash
# 06 — Iterative pre-dump: copy memory while the process runs, so the final
# freeze only has to save the pages that changed. This is how live migration
# keeps downtime short.
source "$(dirname "$0")/common.sh"
init 06_pre_dump
CLEANUP_PATTERNS=("python3 bigmem.py")
command -v jq >/dev/null || { apt-get install -y -qq jq >/dev/null 2>&1 || true; }

cat > bigmem.py <<'EOF'
import os, time
buf = bytearray(os.urandom(1 << 30))   # 1 GiB of incompressible memory
i = 0
while True:                            # keep dirtying a small 4 MiB window
    off = (i * (4 << 20)) % len(buf)
    buf[off:off + (4 << 20)] = os.urandom(4 << 20)
    i += 1
    print(f"tick {i}", flush=True)
    time.sleep(0.2)
EOF

setsid python3 bigmem.py > out.log 2>&1 < /dev/null &
PID=$(wait_pid "python3 bigmem.py")
until grep -q tick out.log 2>/dev/null; do sleep 0.5; done   # wait for the 1 GiB to be filled
sleep 1

stats() {  # frozen time = how long the process was stopped during that dump
  crit show "$1/stats-dump" | jq -r '.entries[0].dump |
    "frozen \(.frozen_time/1000 | floor) ms, pages written \(.pages_written) (\(.pages_written*4/1024 | floor) MiB)"'
}

step "Baseline: one plain dump of a 1 GiB process (--leave-running so we can continue)"
mkdir full
run "criu dump -t $PID -D full -o dump.log --leave-running"
echo "plain dump  : $(stats full)"

step "pre-dump #1: copies everything, process keeps running"
mkdir pre1
run "criu pre-dump -t $PID -D pre1 -o dump.log --track-mem"
echo "pre-dump #1 : $(stats pre1)"
sleep 2

step "pre-dump #2: only pages dirtied since #1 (kernel soft-dirty tracking)"
mkdir pre2
run "criu pre-dump -t $PID -D pre2 -o dump.log --track-mem --prev-images-dir ../pre1"
echo "pre-dump #2 : $(stats pre2)"
sleep 2

step "Final dump: freeze and save only what changed since #2"
mkdir final
run "criu dump -t $PID -D final -o dump.log --track-mem --prev-images-dir ../pre2"
echo "final dump  : $(stats final)"
run "du -sh full pre1 pre2 final"
note "final/ links to pre2/, which links to pre1/; restore reads the whole chain"

step "Restore from the chain"
run "criu restore -D final -d -o restore.log"
sleep 1
run "tail -n 2 out.log"
