# Model:
# - Allowed globals: {Model, Foo, Bar}
# - Allowed callables: {}

class Foo(object):
    pass

class Bar(object):
    pass

class Baz(object):
    pass

class Model(object):

    name: Foo
    value: Bar
