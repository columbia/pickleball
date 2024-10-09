# Model:
# - Allowed globals: {Model, Foo, Bar}
# - Allowed callables: {}

import math
class Foo(object):
    def __init__(self, x):
        self.x = x

class Bar(object):
    pass

class Model(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __setstate__(self, state):
        self.__dict__.update(state)

        # this is realized by cpg.method analysis (local variables)
        d = Foo(1)
        #e = math.sqrt(10)

        # this is infered by the Joern's 'type-recovery
        self.c = Bar()
