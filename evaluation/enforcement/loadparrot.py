import argparse
from pathlib import Path

from parrot import Parrot
from pklballcheck import collect_attr_stats, verify_loader_was_used

TEST = "Can you recommend some upscale restaurants in New York?"


def load_model(model_path, test=TEST) -> bool:

    model_dir = Path(model_path).parent

    try:
        parrot = Parrot(model_tag=str(model_dir), use_gpu=False)
        para_phrases = parrot.augment(input_phrase=test)
        print(para_phrases)

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return True
    finally:
        collect_attr_stats(parrot)


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=("Path to the model (pytorch_model.bin)."),
    )
    parser.add_argument(
        "--test",
        default="Can you recommed some upscale restaurants in Newyork?",
        help=("test input for the model (current string type)"),
    )
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (parent directory of pytorch_model.bin file) and test input"
        )
        exit(1)

    load_model(args.model_path, args.test)
