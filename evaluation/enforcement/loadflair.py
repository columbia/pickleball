import argparse

from flair.data import Sentence
from flair.models import SequenceTagger
from pklballcheck import collect_attr_stats, verify_loader_was_used

TEST = "The experienced professor from Harvard University quickly analyzed the ancient manuscript while drinking coffee in New York last Sunday."


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
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (pytorch_model.bin file) and (optional) test input"
        )
        exit(1)

    is_success, output = load_model(args.model_path)
    print(output)
    verify_loader_was_used()
