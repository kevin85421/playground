class Example:
    def __init__(self):
        self.existing = "I exist"
    
    def __getattribute__(self, name):
        # 每次訪問屬性都會先經過這裡
        print(f"__getattribute__ called with: {name}")
        # 使用 object.__getattribute__ 避免無限遞迴
        return object.__getattribute__(self, name)
    
    def __getattr__(self, name):
        # 只有當常規屬性查找失敗時，才會調用此方法
        print(f"__getattr__ called with: {name}")
        if name == "dynamic":
            return "I am dynamic!"
        # 如果屬性無法處理，則丟出 AttributeError
        raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")

# 建立物件
e = Example()

# 情況 1：訪問已存在的屬性 "existing"
# 調用流程：首先調用 __getattribute__，直接從 __dict__ 中取得屬性，不觸發 __getattr__
print("Case 1: e.existing which is exist in __dict__")
print(e.existing)
print("-" * 50)

# 情況 2：訪問不存在但能由 __getattr__ 處理的屬性 "dynamic"
# 調用流程：首先調用 __getattribute__ 因為 "dynamic" 不存在，之後觸發 __getattr__ 返回預設值
print("Case 2: e.dynamic which is not exist in __dict__, but can be handled by __getattr__")
print(e.dynamic)
print("-" * 50)

# 情況 3：使用內建函數 getattr 存取屬性，對已存在屬性
# 調用流程：與直接存取類似，先走 __getattribute__
print("Case 3: getattr existing attribute")
print(getattr(e, "existing"))
print("-" * 50)

# 情況 4：使用內建函數 getattr 存取不存在的屬性，並提供預設值
# 調用流程：如果屬性不存在，先走 __getattribute__（查找失敗後），然後由 __getattr__ 處理；
# 但因為我們提供了預設值，所以不會拋出異常
print("Case 4: getattr non-existent attribute")
print(getattr(e, "non_existent", "default value"))
