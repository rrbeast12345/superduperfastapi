import time
class example:
    def __init__(self, name, age):
        self.name = name
        self.age = age
one = example('oliver', 7)
setattr(one, "color", "blue")
for item in vars(one):
    print(item)
print(vars(one))
print(time.time())
