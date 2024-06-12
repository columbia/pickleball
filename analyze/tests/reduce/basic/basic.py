# Intended inferred policy:
# ALLOWED_CLASSES: {str, int}
# ALLOWED_REDUCES: {create_person}

def create_person(name: str, age: int):
    return Person(name, age)

class Person(object):

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def __reduce__(self):
        return (create_person, (self.name, self.age))
