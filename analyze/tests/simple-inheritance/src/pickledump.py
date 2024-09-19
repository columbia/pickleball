import pickle

import model

if __name__ == "__main__":

    optimizer = model.SGD(value=42)
    #tensor = model.Tensor("tensor-name", [1,2,3,4])
    tensor = model.SpecializedTensor("tensor-name", [1,2,3,4])
    baz = model.Baz()

    model_obj = model.SpecializedModel("model-name", optimizer, tensor, baz, "special-name")

    with open("model.pkl", "wb") as fd:
        pickle.dump(model_obj, fd)

    optimizer2 = model.Optimizer()
    tensor2 = model.Tensor("tensor-name", [1,2,3,4])
    baz2 = model.Baz()

    model_obj2 = model.SpecializedModel("model-name2", optimizer2, tensor2, baz2, "special-name2")
    with open("model2.pkl", "wb") as fd:
        pickle.dump(model_obj2, fd)
