from parrot import Parrot
import argparse

def load_model(model_path, test=""):
    try:
        parrot = Parrot(model_tag=model_path, use_gpu=False)
        para_phrases = parrot.augment(input_phrase=test)
        print(para_phrases)

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
            "Path to the model (parent of pytorch_model.bin)."
        ),
    )
    parser.add_argument(
        "--test",
        default="Can you recommed some upscale restaurants in Newyork?",
        help=(
            "test input for the model (current string type)"
        ),
    )
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (parent of pytorch_model.bin file) and test input")
        exit(1)

    load_model(args.model_path, args.test)
