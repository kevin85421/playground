"""Run a command as a "child subreaper" that reaps every orphaned descendant.

Why: CRIU restores a process with the SAME PID it had. If an old process with
that PID is still a zombie, restore fails with "Can't fork for <pid>: File
exists". Orphans are normally reaped by PID 1, but a container whose PID 1 is
`sleep infinity` never reaps anything, so zombies pile up and hold their PIDs.

With PR_SET_CHILD_SUBREAPER, orphans inside our subtree (e.g. a process that
`criu restore -d` left behind) are reparented to us instead of PID 1, and we
reap them. When the command exits we also kill whatever it left running.
"""

import ctypes
import os
import signal
import sys
import time

PR_SET_CHILD_SUBREAPER = 36
ctypes.CDLL(None, use_errno=True).prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0)

me = os.getpid()
cmd = os.fork()
if cmd == 0:
    os.execvp(sys.argv[1], sys.argv[1:])


def children():
    out = []
    for p in os.listdir("/proc"):
        if p.isdigit():
            try:
                with open(f"/proc/{p}/stat") as f:
                    if int(f.read().rsplit(")", 1)[1].split()[1]) == me:
                        out.append(int(p))
            except (OSError, IndexError, ValueError):
                pass
    return out


code = 0
while True:
    try:
        pid, status = os.wait()
    except ChildProcessError:
        break
    if pid == cmd:
        code = os.waitstatus_to_exitcode(status)
        for _ in range(20):  # kill leftovers (and their re-parented children)
            left = children()
            if not left:
                break
            for c in left:
                try:
                    os.kill(c, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            while True:
                try:
                    if os.waitpid(-1, os.WNOHANG)[0] == 0:
                        break
                except ChildProcessError:
                    break
            time.sleep(0.05)
sys.exit(code)
