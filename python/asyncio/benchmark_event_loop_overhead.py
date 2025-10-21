import asyncio
import time

def benchmark_event_loop_overhead(iterations: int):
    creation_times = []
    closing_times = []

    for _ in range(iterations):
        # Measure creation time
        start_create = time.perf_counter()
        loop = asyncio.new_event_loop()
        end_create = time.perf_counter()
        creation_times.append(end_create - start_create)

        # Measure closing time
        start_close = time.perf_counter()
        loop.close()
        end_close = time.perf_counter()
        closing_times.append(end_close - start_close)

    avg_creation_time = sum(creation_times) / iterations
    avg_closing_time = sum(closing_times) / iterations

    print(f"Average event loop creation overhead: {avg_creation_time * 1000:.4f} ms")
    print(f"Average event loop closing overhead: {avg_closing_time * 1000:.4f} ms")

if __name__ == "__main__":
    benchmark_event_loop_overhead(1000000)