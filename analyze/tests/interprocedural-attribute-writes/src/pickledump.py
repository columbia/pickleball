import pickle

import model

if __name__ == "__main__":

    m = model.Model()
    trainer = model.Trainer(m)
    optimizer = model.SGD()
    trainer.train('test-trainer', optimizer)
    with open("model.pkl", "wb") as fd:
        pickle.dump(m, fd)
