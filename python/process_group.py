import argparse
import os
import signal
import subprocess
import sys
import time


def _make_child_code() -> str:
    # Child prints its IDs, handles SIGTERM/SIGINT gracefully, and loops.
    return r'''
import os, sys, time, signal

def _handle(sig, _):
    print(f"[child] got signal {sig}, exiting...", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, _handle)
signal.signal(signal.SIGINT, _handle)

print(f"[child] pid={os.getpid()} ppid={os.getppid()} pgid={os.getpgid(0)}", flush=True)
while True:
    time.sleep(1)
'''


def _make_leader_code(child_code: str) -> str:
    # Leader spawns the child and loops. It does not handle SIGTERM/KILL specially.
    return rf'''
import os, sys, time, subprocess

print(f"[leader] pid={{os.getpid()}} pgid={{os.getpgid(0)}}", flush=True)
child = subprocess.Popen([sys.executable, "-u", "-c", r"""{child_code}"""])

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
'''


def cleanup_process_group(pgid: int) -> None:
    print(f"[monitor] sending SIGTERM to process group {pgid}...", flush=True)
    os.killpg(pgid, signal.SIGTERM)

def run_demo(sleep_before_kill: float, use_process_group: bool, use_kill_pg: bool) -> int:
    child_code = _make_child_code()
    leader_code = _make_leader_code(child_code)

    print(f"[monitor] starting leader in a NEW SESSION/PROCESS GROUP... (sleep_before_kill: {sleep_before_kill}, use_process_group: {use_process_group})", flush=True)
    if use_process_group:
        leader = subprocess.Popen(
        [sys.executable, "-u", "-c", leader_code],
            preexec_fn=os.setsid,  # new session -> leader's pid == pgid
        )
    else:
        leader = subprocess.Popen(
            [sys.executable, "-u", "-c", leader_code],
        )

    print(f"[monitor] leader pid={leader.pid}", flush=True)
    print(f"[monitor] sleeping for {sleep_before_kill} seconds to wait for the child process to start...", flush=True)
    time.sleep(max(0.5, sleep_before_kill))

    if not use_kill_pg:
        print("[monitor] sending SIGKILL to leader only...", flush=True)
        try:
            os.kill(leader.pid, signal.SIGKILL)
        except ProcessLookupError:
            print("[monitor] leader already exited before SIGKILL was sent.")
        # Ensure leader is reaped
        try:
            leader.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("[monitor] WARNING: leader did not exit promptly after SIGKILL.")
    else:
        print("[monitor] cleaning up its process group...", flush=True)
        pgid = leader.pid
        cleanup_process_group(pgid)
    print("[monitor] done.", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Process group cleanup demo")
    parser.add_argument(
        "--sleep-before-kill",
        type=float,
        default=1.0,
        help="Seconds to wait after leader start before sending SIGKILL",
    )
    parser.add_argument(
        "--use-process-group",
        action=argparse.BooleanOptionalAction,
        help="Use process group",
    )
    parser.add_argument(
        "--use-kill-pg",
        action=argparse.BooleanOptionalAction,
        help="Use killpg",
    )
    args = parser.parse_args()
    print(f"[monitor] args: {args}", flush=True)
    assert not (not args.use_process_group and args.use_kill_pg), "doesn't use process group and call `os.killpg`"
    return run_demo(args.sleep_before_kill, args.use_process_group, args.use_kill_pg)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        # If the user interrupts manually, just exit.
        raise


