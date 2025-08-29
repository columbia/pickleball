import argparse
from pathlib import Path

from pklballcheck import collect_attr_stats, verify_loader_was_used
from tner import TransformersNER

TEST = "The happy man has been eating at the diner"


def load_model(model_path, test=TEST) -> bool:

    model_dir = Path(model_path).parent
    print(f"model_dir: {model_dir}")
    try:
        model = TransformersNER(str(model_dir))
        print(
            model.predict(
                ["Jacob Collier is a Grammy awarded English artist from London"]
            )
        )
    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        collect_attr_stats(model)
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
            "ERROR: need to specify model path (parent directory of pytorch_model.bin file) and (optional) test input"
        )
        exit(1)

    load_model(args.model_path, args.test)
