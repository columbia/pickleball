import pickle

import model

if __name__ == "__main__":

    optimizer = model.SGD(value=42)
    #tensor = model.Tensor("tensor-name", [1,2,3,4])
    tensor = model.SpecializedTensor("tensor-name", [1,2,3,4])
    baz = model.Baz()

    model_obj = model.SpecializedModel("model-name", optimizer, tensor, baz, "special-name")
    model_obj.bar = model.Bar()

    with open("model.pkl", "wb") as fd:
        pickle.dump(model_obj, fd)
