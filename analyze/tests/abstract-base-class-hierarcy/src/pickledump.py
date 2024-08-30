import pickle

import model

if __name__ == "__main__":

    sequence_tagger = model.SequenceTagger()
    sequence_tagger.set_model_card(model.Sentence("this is a sentence"))

    with open("model.pkl", "wb") as fd:
        pickle.dump(sequence_tagger, fd)
