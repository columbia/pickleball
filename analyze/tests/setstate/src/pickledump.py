import pickle

import model

if __name__ == "__main__":

    model_obj = model.Model(0, 0)

    with open("model.pkl", "wb") as fd:
        pickle.dump(model_obj, fd)
