
def rebuild_tensor():
    return Tensor()

class Foo(object):
    pass

class Bar(object):
    pass

class Tensor(object):

    def __reduce__(self):
        return (rebuild_tensor, ())

class ParentModel(object):

    def __init__(self, foo: Foo, tensor: Tensor):
        self.foo = foo
        self.tensor = tensor
