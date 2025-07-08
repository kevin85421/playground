import asyncio
import time


async def bad_blocking():
    print("Start")
    time.sleep(3)  # ⚠️ 錯誤！這是 blocking！
    # 正確作法
    # await asyncio.sleep(3)
    print("End")


async def main():
    await asyncio.gather(bad_blocking(), bad_blocking())


start = time.time()
asyncio.run(main())
end = time.time()
print(f"Time taken: {end - start} seconds")
