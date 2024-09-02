import pickle

import basic

if __name__ == "__main__":

    model_obj = basic.Person('name', 42)

    with open("model.pkl", "wb") as fd:
        pickle.dump(model_obj, fd)
