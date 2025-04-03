import tweetnlp
from pklballcheck import verify_loader_was_used
import argparse

def load_model(model_path, test=""):
    try:
        model = tweetnlp.Classifier(model_path, max_length=128)
        pre = model.predict(test)

        print(pre)

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")



if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=(
            "Path to the model (directory containing pytorch_model.bin and config.json)."
        ),
    )
    parser.add_argument(
        "--test",
        default="The happy man has been eating at the diner",
        help=(
            "test input for the model (string type)"
        ),
    )
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (directory containing pytorch_model.bin and config) and test input")
        exit(1)

    load_model(args.model_path, args.test)
    verify_loader_was_used()
