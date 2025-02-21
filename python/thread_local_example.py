import threading
import time

# Create a thread-local storage object
thread_local_data = threading.local()


def worker():
    # Set a unique attribute value for each thread
    thread_local_data.value = threading.current_thread().name
    print(f"{threading.current_thread().name} set value: {thread_local_data.value}")

    # Simulate some work
    time.sleep(1)

    # Read the stored value for the same thread
    print(f"{threading.current_thread().name} read value: {thread_local_data.value}")


threads = []
for i in range(3):
    t = threading.Thread(target=worker, name=f"Worker-{i}")
    threads.append(t)
    t.start()

# Wait for all threads to finish
for t in threads:
    t.join()
