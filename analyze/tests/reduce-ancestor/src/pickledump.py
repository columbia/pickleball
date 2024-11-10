import pickle

import model

if __name__ == "__main__":

    model_obj = model.Child(10)

    with open("model.pkl", "wb") as fd:
        pickle.dump(model_obj, fd)
