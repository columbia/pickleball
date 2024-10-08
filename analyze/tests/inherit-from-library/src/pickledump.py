import pickle

import model
import parentmodel

if __name__ == "__main__":

    tensor = parentmodel.Tensor()

    model_obj = model.Model(parentmodel.Foo(), tensor)

    with open("model.pkl", "wb") as fd:
        pickle.dump(model_obj, fd)
