class Parent(object):

    def __init__(self):
        self._value_ = 42

    def __reduce_ex__(self, proto):
        return self.__class__, (self._value_, )


class Child(Parent):

    def __init__(self, value):
        self._value_ = value
