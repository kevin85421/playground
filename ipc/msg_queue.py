from multiprocessing import Process, Queue
import time


def producer(queue):
    for i in range(5):
        print(f"[Producer] 放入：{i}")
        queue.put(i)
        time.sleep(0.5)
    queue.put(None)  # 發送結束訊號


def consumer(queue):
    while True:
        item = queue.get()
        if item is None:
            print("[Consumer] 收到結束訊號，退出")
            break
        print(f"[Consumer] 拿到：{item}")


if __name__ == '__main__':
    q = Queue()
    p1 = Process(target=producer, args=(q,))
    p2 = Process(target=consumer, args=(q,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
