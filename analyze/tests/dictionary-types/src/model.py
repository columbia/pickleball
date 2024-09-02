class Optimizer(object):
    pass

class Model(object):

    def __init__(self, optimizer: Optimizer):
        # Type should be recovered: dict<string, string|Optimizer|int>
        #self.model_card = {'name': 'model', 'optimizer': optimizer, 'value': 1}
        self.model_card = {}
        self.model_card['name'] = 'model'
        self.model_card['optimizer'] = optimizer
        self.model_card['value'] = 1
