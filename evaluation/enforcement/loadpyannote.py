import argparse
from pathlib import Path

from pklballcheck import collect_attr_stats, verify_loader_was_used
from pyannote.audio import Inference, Model
from pyannote.core import Segment

DIR = Path(__file__).parent
TEST_FILE = DIR / Path("test-pyannote") / Path("test.wav")


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
        # collect_attr_stats(model)
        return True, output.data


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=("Path to the model (pytorch_model.bin)."),
    )
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (pytorch_model.bin file). No test is needed."
        )
        exit(1)

    is_success, output = load_model(args.model_path)
    print(output)
    verify_loader_was_used()
