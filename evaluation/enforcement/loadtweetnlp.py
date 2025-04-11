import argparse
from pathlib import Path

import tweetnlp
from pklballcheck import collect_attr_stats, verify_loader_was_used

TEST = "The happy man has been eating at the diner"


def load_model(model_path, test=TEST) -> tuple[bool, str]:
    model_dir = Path(model_path).parent

    try:
        model = tweetnlp.Classifier(str(model_dir), max_length=128)
        pre = model.predict(test)

        # print(pre)

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False, ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        collect_attr_stats(model)
        return True, pre


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=(
            "Path to the model (pytorch_model.bin, in same directory as config.json)."
        ),
    )
    parser.add_argument(
        "--test",
        default="The happy man has been eating at the diner",
        help=("test input for the model (string type)"),
    )
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (directory containing pytorch_model.bin and config) and test input"
        )
        exit(1)

    is_success, output = load_model(args.model_path, args.test)
    print(output)
    # verify_loader_was_used()
