import argparse
import os
from pathlib import Path

from pyannote.audio import Inference, Model
from pyannote.core import Segment

try:
    from pklballcheck import collect_attr_stats, verify_loader_was_used
except:
    pass

DIR = Path(__file__).parent
TEST_FILE = DIR / Path("test-pyannote") / Path("test.wav")
VALIDATION_DIR = Path("/datasets/aishell-4/wav")


def validate_model(model_path) -> str:

    validation_files = os.listdir(VALIDATION_DIR)

    try:
        model = Model.from_pretrained(model_path)

        inference = Inference(model, step=2.5)

        all_output = ""
        for file in validation_files:
            output = inference(str(VALIDATION_DIR / file))
            print(file)
            print(output.data)
            all_output = file + "\n" + output.data + "\n"

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return all_output


def load_model(model_path) -> tuple[bool, str]:

    try:
        model = Model.from_pretrained(model_path)

        inference = Inference(model, step=2.5)
        output = inference(str(TEST_FILE))
        # print(output.data.shape)

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False, ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return True, output.data


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=("Path to the model (pytorch_model.bin)."),
    )
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (pytorch_model.bin file). No test is needed."
        )
        exit(1)

    if args.validate:
        validate_model(args.model_path)
    else:
        is_success, output = load_model(args.model_path)
        print(output)
    verify_loader_was_used()
