# Model:
# - Allowed globals: {Model, Optimizer, Baz}
# - Allowed callables: {create_tensor}


def create_tensor(name: str, values):
    return Tensor(name, values)

class Foo(object):
    pass

class Bar(object):
    pass

class Baz(object):
    pass

class Tensor(object):

    def __init__(self, name: str, values):
        self.name = name
        self.values = values

    def __reduce__(self):
        return (create_tensor, ((self.name), [1, 2, 3, 4]))

class Optimizer(object):

    def __init__(self):
        self.foo = Foo()


class Model(object):

    def __init__(self, name: str, optimizer: Optimizer, tensor: Tensor, baz: Baz):
        self.name = name
        self.optimizer = optimizer
        self.tensor = tensor
        self.model_card = {}
        self.model_card['optimizer'] = baz
