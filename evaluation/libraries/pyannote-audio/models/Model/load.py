import argparse
from pklballcheck import verify_loader_was_used
from pyannote.audio import Model, Inference
from pyannote.core import Segment

def load_model(model_path):

    try:
        model = Model.from_pretrained(model_path)

        inference = Inference(model, step=2.5)
        output = inference("sample.wav")
        print(output.data.shape)

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=(
            "Path to the model (pytorch_model.bin)."
        ),
    )
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (pytorch_model.bin file). No test is needed.")
        exit(1)

    load_model(args.model_path)
    verify_loader_was_used()
