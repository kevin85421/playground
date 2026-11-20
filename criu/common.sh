# Shared helpers for the CRIU examples. Each example does:
#   source "$(dirname "$0")/common.sh"; init <name>
# and then works inside $WORK (a fresh directory per example).

set -euo pipefail

EXAMPLES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Re-run the example under reaper.py so orphans/zombies never keep a PID busy
# (see reaper.py for why this matters when the container's PID 1 is `sleep`).
if [ "${CRIU_EXAMPLE_REAPER:-}" != 1 ]; then
  export CRIU_EXAMPLE_REAPER=1
  exec python3 "$EXAMPLES_DIR/reaper.py" bash "$0" "$@"
fi

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
note() { printf '\033[2m    # %s\033[0m\n' "$*"; }
run()  { printf '\033[1;33m$ %s\033[0m\n' "$*"; eval "$@"; }

# Wait until a process whose command line matches $1 exists, print its PID.
wait_pid() {
  local pattern=$1 pid=""
  for _ in $(seq 1 50); do
    pid=$(pgrep -f -- "$pattern" | head -1 || true)
    [ -n "$pid" ] && { echo "$pid"; return 0; }
    sleep 0.1
  done
  echo "process matching '$pattern' did not start" >&2
  return 1
}

alive() { kill -0 "$1" 2>/dev/null; }

init() {
  [ "$(id -u)" = 0 ] || { echo "run as root (CRIU needs CAP_SYS_ADMIN)"; exit 1; }
  command -v criu >/dev/null || { echo "criu not installed"; exit 1; }
  NAME=$1
  WORK=${WORK_ROOT:-/tmp/criu-examples}/$NAME
  rm -rf "$WORK"; mkdir -p "$WORK"; cd "$WORK"
  printf '\033[1m### %s  (work dir: %s)\033[0m\n' "$NAME" "$WORK"
  CLEANUP_PATTERNS=()
  trap cleanup EXIT
}

# Kill any process the example started, so examples can run back to back.
cleanup() {
  for p in "${CLEANUP_PATTERNS[@]:-}"; do
    [ -n "$p" ] && pkill -f -- "$p" 2>/dev/null || true
  done
}
