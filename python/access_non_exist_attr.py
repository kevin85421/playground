class MyClass:
    def __init__(self):
        self.hello = "hello"
        self.world = "world"

    def __del__(self):
        print("Call __del__")
        self.hello

    def __getattr__(self, name):
        # 如果 world 不存在於 __dict__ 中，則會呼叫 __getattr__
        # 但會不停 recursive。
        if self.world == "world":
            return name


obj = MyClass()
# {'hello': 'hello', 'world': 'world'}
print(obj.__dict__)

# 移除 hello 和 world
del obj.hello
del obj.world

# 不停 recursive
del obj
