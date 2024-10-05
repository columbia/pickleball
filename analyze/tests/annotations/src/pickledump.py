import pickle

import model

if __name__ == "__main__":

    model_obj = model.Model()
    model_obj.name = model.Foo()
    model_obj.value = model.Bar()

    with open("model.pkl", "wb") as fd:
        pickle.dump(model_obj, fd)
