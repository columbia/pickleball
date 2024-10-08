"""
Globals: {Model, Foo, rebuild_tensor}
Reduces: {rebuild_tensor}
"""

import parentmodel

class Model(parentmodel.ParentModel):

    def __init__(self, foo: parentmodel.Foo, tensor: parentmodel.Tensor):
        super().__init__(foo, tensor)
