# SpecializedModel:
# - Allowed globals: {Child, Value, ParentValue, GrandparentValue}
# - Allowed callables: {}

class Value(object):
    pass

class ParentValue(object):
    pass

class GrandparentValue(object):
    pass

class Grandparent(object):

    def __init__(self):
        self.grandparent_value = GrandparentValue()

class Parent(Grandparent):

    def __init__(self):
        self.parent_value = ParentValue()
        super().__init__()

class Child(Parent):

    def __init__(self):
        self.value = Value()
        super().__init__()
