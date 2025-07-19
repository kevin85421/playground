import os

r, w = os.pipe()

pid = os.fork()
if pid == 0:  # child
    os.close(r)
    os.write(w, b"Hello from child")
    os._exit(0)
else:  # parent
    os.close(w)
    print(os.read(r, 100).decode())
