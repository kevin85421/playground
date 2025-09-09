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