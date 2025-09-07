import attrs

@attrs.define
class Person:
    name: str
    age: int
    email: str = ""

print("Print a `Person` instance which is annotated by `attrs.define`")
person = Person("Alice", 30, "alice@example.com")
print(person)

class Person2:
    def __init__(self, name, age, email):
        self.name = name
        self.age = age
        self.email = email

print("Print a `Person2` instance which is not annotated by `attrs.define`")
person2 = Person2("Alice", 30, "alice@example.com")
print(person2)