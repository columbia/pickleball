import pickle

import model

if __name__ == "__main__":
    optimizer = model.Optimizer
    tensor = model.Tensor("tensor-name", [1,2,3,4])
    model_obj = model.Model("model-name", optimizer, tensor)
    #serialized = pickle.dumps(model_obj)
    with open("model.pkl", "wb") as fd:
        pickle.dump(model_obj, fd)
