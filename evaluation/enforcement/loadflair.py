import argparse

from flair.data import Sentence
from flair.models import SequenceTagger
from pklballcheck import collect_attr_stats, verify_loader_was_used

TEST = "I love berlin."

def load_model(model_path, test=TEST) -> bool:
    try:
        tagger = SequenceTagger.load(model_path)
        sentence = Sentence(test)

        tagger.predict(sentence)

        # for entity in sentence.get_spans('np'):
        #    print(entity)
    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        collect_attr_stats(tagger)
        return True


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
