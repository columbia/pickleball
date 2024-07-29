import pickle

import model

if __name__ == "__main__":

    optimizer = model.Optimizer
    tensor = model.Tensor("tensor-name", [1,2,3,4])
    baz = model.Baz()

    model_obj = model.Model("model-name", optimizer, tensor, baz)

    with open("model.pkl", "wb") as fd:
        pickle.dump(model_obj, fd)
