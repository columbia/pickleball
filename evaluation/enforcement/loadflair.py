import argparse

import flair.datasets
from flair.data import MultiCorpus, Sentence
from flair.models import SequenceTagger

try:
    from pklballcheck import collect_attr_stats, verify_loader_was_used
except:
    pass

NUM_VALIDATE_SENTENCES = 1000


TEST = "The experienced professor from Harvard University quickly analyzed the ancient manuscript while drinking coffee in New York last Sunday."


def validate_model(model_path) -> str:

    ner_english_corpus = flair.datasets.NER_ENGLISH_PERSON()
    ner_german_corpus = flair.datasets.NER_GERMAN_GERMEVAL()
    up_spanish_corpus = flair.datasets.UP_SPANISH()
    ud_dutch_corpus = flair.datasets.UD_DUTCH()
    ud_french_corpus = flair.datasets.UD_FRENCH()
    ud_german_corpus = flair.datasets.UD_GERMAN()
    ud_arabic_corpus = flair.datasets.UD_ARABIC()

    corpus_map = {
        "flair-ner-english": ner_english_corpus,
        "flair-ner-english-fast": ner_english_corpus,
        "flair-ner-english-large": ner_english_corpus,
        "flair-chunk-english-fast": ner_english_corpus,
        "flair-ner-english-ontonotes": ner_english_corpus,
        "flair-ner-english-ontonotes-large": ner_english_corpus,
        "flair-ner-english-ontonotes-fast": ner_english_corpus,
        "flair-ner-spanish-large": up_spanish_corpus,
        "flair-ner-dutch-large": ud_dutch_corpus,
        "flair-ner-french": ud_french_corpus,
        "flair-ner-german": ud_german_corpus,
        "flair-ner-german-large": ud_german_corpus,
        "megantosh-flair-arabic-multi-ner": ud_arabic_corpus,
        "flair-upos-english": ner_english_corpus,
        "flair-pos-english": ner_english_corpus,
        "flair-pos-english-fast": ner_english_corpus,
        "flair-upos-english-fast": ner_english_corpus,
        "flair-ner-multi": MultiCorpus(
            [
                ner_english_corpus,
                ner_german_corpus,
                ud_dutch_corpus,
            ]
        ),
        "flair-upos-multi": MultiCorpus(
            [
                ner_english_corpus,
                ner_german_corpus,
                ud_dutch_corpus,
            ]
        ),
    }

    model_name = model_path.split("/")[-2]
    corpus = corpus_map[model_name]

    sentences = corpus.get_all_sentences()
    print(f"Total sentences: {len(sentences)}")
    try:
        model = SequenceTagger.load(model_path)
        all_output = ""
        total_sentences_tested = 0
        for sentence in sentences[:10]:

            model.predict(sentence)

            entities = sentence.get_spans()
            output = "\n".join([str(entity) for entity in entities])

            # If we are running a POS model the spans will be empty and the tags
            # will be incorporated in the sentence
            if len(output) == 0:
                output = sentence

            output = str(output) + "\n"

            # print(output)
            all_output += output
            total_sentences_tested += 1

            if total_sentences_tested >= NUM_VALIDATE_SENTENCES:
                break

    except Exception as e:
        print(f"\033[91mFAILED in {model_name}\033[0m")
        print(e)
        return ""
    else:
        print(f"\033[92mSUCCEEDED in {model_name}\033[0m")
        return all_output


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
        #collect_attr_stats(tagger)
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
        output = validate_model(args.model_path)
        print(output)
    else:
        is_success, output = load_model(args.model_path)
        print(output)
        verify_loader_was_used()
