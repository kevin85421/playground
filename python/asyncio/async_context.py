import asyncio


class AsyncResource:
    """Simple example demonstrating __aenter__ and __aexit__."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def __aenter__(self):
        """Called when entering 'async with' block."""
        print(f"__aenter__: Setting up {self.name}")
        await asyncio.sleep(1)  # Simulate async setup
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Called when exiting 'async with' block."""
        print(f"__aexit__: Cleaning up {self.name}")
        await asyncio.sleep(1)  # Simulate async cleanup
        return False  # Don't suppress exceptions


async def main():
    # Using async context manager
    print("This should be printed before the __aenter__")
    async with AsyncResource("resource1") as resource:
        print(f"Using {resource.name} => This should be printed after __aenter__ and before __aexit__")
    print("This should be printed after the __aexit__")


if __name__ == "__main__":
    asyncio.run(main())
