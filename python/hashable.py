class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

d = {Person("Alice", 20): "value"}
print("Person('Alice', 20) in d: ", Person("Alice", 20) in d) # False

class Person2:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    def __hash__(self):
        return hash((self.name, self.age))

d2 = {Person2("Alice", 20): "value"}
print("Person2('Alice', 20) in d2: ", Person2("Alice", 20) in d2) # False

class Person3:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    def __hash__(self):
        return hash((self.name, self.age))
    def __eq__(self, other):
        return self.name == other.name and self.age == other.age

d3 = {Person3("Alice", 20): "value"}
print("Person3('Alice', 20) in d3: ", Person3("Alice", 20) in d3) # True

# 驗證 set update() 不會改變原本 set 中的 instance。
alice1 = Person3("Alice", 20)
id1 = id(alice1)
alice2 = Person3("Alice", 20)
id2 = id(alice2)
s = set([alice1])
assert alice2 in s
s.update([alice2])

l = list(s)
assert len(l) == 1
assert l[0] is alice1
assert l[0] is not alice2
