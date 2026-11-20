#!/usr/bin/env bash
# 05 — A live TCP connection survives a dump/restore of one end (--tcp-established).
source "$(dirname "$0")/common.sh"
init 05_tcp
CLEANUP_PATTERNS=("python3 server.py" "python3 client.py")

cat > server.py <<'EOF'
import socket
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", 5555)); s.listen()
conn, addr = s.accept()
print(f"server: accepted {addr}", flush=True)
for line in conn.makefile():
    conn.sendall(f"pong {line.split()[1]}\n".encode())
EOF

cat > client.py <<'EOF'
import socket, time
c = socket.create_connection(("127.0.0.1", 5555))
port = c.getsockname()[1]
f = c.makefile()
i = 0
while True:
    i += 1
    c.sendall(f"ping {i}\n".encode())
    print(f"client (local port {port}): sent ping {i}, got {f.readline().strip()}", flush=True)
    time.sleep(1)
EOF

setsid python3 server.py > server.log 2>&1 < /dev/null &
wait_pid "python3 server.py" > /dev/null; sleep 0.5
setsid python3 client.py > client.log 2>&1 < /dev/null &
CLIENT=$(wait_pid "python3 client.py")
sleep 3
run "tail -n 2 client.log"
run "ss -tnp | grep 5555"

step "Dump only the client. Without --tcp-established CRIU refuses:"
mkdir img
run "criu dump -t $CLIENT -D img -o dump-refused.log || echo '>>> dump refused (expected)'"
run "grep -m1 -i 'established' img/dump-refused.log"

step "With --tcp-established CRIU uses TCP_REPAIR to save sequence numbers and queued data"
note "--network-lock nftables: block the connection's packets while it is frozen (iptables is not installed here)"
run "criu dump -t $CLIENT -D img -o dump.log --tcp-established --network-lock nftables"
note "the server still holds its end; it just sees silence"
sleep 3

step "Restore the client: same local port, same connection, the counter continues"
run "criu restore -D img -d -o restore.log --tcp-established --network-lock nftables"
sleep 3
run "tail -n 4 client.log"
run "ss -tnp | grep 5555"
