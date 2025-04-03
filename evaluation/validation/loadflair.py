import argparse

import flair.datasets
from flair.data import Sentence
from flair.models import SequenceTagger
from pklballcheck import collect_attr_stats, verify_loader_was_used

corpus_map = {
    "flair-ner-english": flair.datasets.NER_ENGLISH_PERSON,
    "flair-ner-english-fast": flair.datasets.NER_ENGLISH_PERSON,
    "flair-ner-english-large": flair.datasets.NER_ENGLISH_PERSON,
    "flair-chunk-english-fast": flair.datasets.NER_ENGLISH_PERSON,
    "flair-ner-english-ontonotes-large": flair.datasets.NER_ENGLISH_PERSON,
    "flair-ner-english-ontonotes-fast": flair.datasets.NER_ENGLISH_PERSON,
    "flair-ner-spanish-large": flair.datasets.UP_SPANISH,
    "flair-ner-dutch-large": flair.datasets.UD_DUTCH,
}


def validate_model(model, model_name):

    corpus = corpus_map[model_name]()

    sentences = corpus.get_all_sentences()
    print(f"Total sentences: {len(sentences)}")
    try:
        for sentence in sentences:

            print(sentence)

            model.predict(sentence)

            for entity in sentence.get_spans():
                print(entity)
    except Exception as e:
        print(f"Error: {e}")


def load_model(model_path, test="") -> bool:

    model_name = model_path.split("/")[-2]

    try:
        tagger = SequenceTagger.load(model_path)

        validate_model(tagger, model_name)
        # print(sentence)

        # for entity in sentence.get_spans('np'):
        #    print(entity)
    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return True
    # finally:
    #     collect_attr_stats(tagger)


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=("Path to the model (pytorch_model.bin)."),
    )
    parser.add_argument(
        "--test",
        default="The happy man has been eating at the diner",
        help=("test input for the model (current string type)"),
    )
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (pytorch_model.bin file) and (optional) test input"
        )
        exit(1)

    load_model(args.model_path, args.test)
    verify_loader_was_used()
