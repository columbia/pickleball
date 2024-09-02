# SpecializedModel:
# - Allowed globals: {SpecializedModel, Optimizer, SGD, Baz}
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

class SpecializedTensor(Tensor):

    def __init__(self, name: str, values):
        super().__init__(name, values)


class Optimizer(object):

    def __init__(self):
        self.foo = Foo()

class SGD(Optimizer):

    def __init__(self, value: int):
        self.value = value

class Model(object):

    def __init__(self, name: str, optimizer: Optimizer, tensor: Tensor, baz: Baz):
        self.name = name
        self.optimizer = optimizer
        self.tensor = tensor
        self.model_card = {}
        self.model_card['optimizer'] = baz

class MixinAttribute(object):
    pass

class SpecialMixin(object):

    def __init__(self):
        self.mixin_attribute = MixinAttribute()

class SpecializedModel(Model, SpecialMixin):

    def __init__(self, name: str, optimizer: Optimizer, tensor: Tensor, baz: Baz, special_name: str):
        self.special_name = special_name
        super().__init__(name, optimizer, tensor, baz)
