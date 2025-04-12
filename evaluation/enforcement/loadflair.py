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


TEST = "The experienced professor from Harvard University quickly analyzed the ancient manuscript while drinking coffee in New York last Sunday."


def validate_model(model_path):

    model_name = model_path.split("/")[-2]
    corpus = corpus_map[model_name]()

    sentences = corpus.get_all_sentences()
    print(f"Total sentences: {len(sentences)}")
    try:
        model = SequenceTagger.load(model_path)
        for sentence in sentences:

            model.predict(sentence)

            entities = sentence.get_spans()
            output = "\n".join([str(entity) for entity in entities])

            # If we are running a POS model the spans will be empty and the tags
            # will be incorporated in the sentence
            if len(output) == 0:
                output = sentence

            print(output)

    except Exception as e:
        print(f"\033[91mFAILED in {model_name}\033[0m")
        print(e)
    else:
        print(f"\033[92mSUCCEEDED in {model_name}\033[0m")


def load_model(model_path, test=TEST) -> tuple[bool, str]:
    try:
        tagger = SequenceTagger.load(model_path)
        sentence = Sentence(test)

        tagger.predict(sentence)

        entities = sentence.get_spans()
        output = "\n".join([str(entity) for entity in entities])

        # If we are running a POS model the spans will be empty and the tags
        # will be incorporated in the sentence
        if len(output) == 0:
            output = sentence

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False, ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        collect_attr_stats(tagger)
        return True, output


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
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (pytorch_model.bin file) and (optional) test input"
        )
        exit(1)

    if args.validate:
        validate_model()
    else:
        is_success, output = load_model(args.model_path)
        print(output)
    verify_loader_was_used()
