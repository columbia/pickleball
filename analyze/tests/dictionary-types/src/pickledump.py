import pickle

import model

if __name__ == "__main__":

    optimizer = model.Optimizer()
    m = model.Model(optimizer)
    with open("model.pkl", "wb") as fd:
        pickle.dump(m, fd)
