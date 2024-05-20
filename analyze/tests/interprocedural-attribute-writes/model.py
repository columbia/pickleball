'''
Need to identify:
    - writes to attributes in methods that are not part of the Model class
    - writes to attributes through dictionary slices
'''

class Model(object):

    def __init__(self):

        self.model_card = None
        self.name = None

class Optimizer(object):
    pass

class SGD(Optimizer):
    pass

class Trainer(object):

    def __init__(self, model: Model):

        self.model = model

    def train(self, name: str, optimizer: Optimizer):

        model_card = {'name': name}

        # Optimizer class included in the model through a dictionary field
        model_card['optimizer'] = optimizer

        self.model.name = name
        self.model.model_card = model_card
