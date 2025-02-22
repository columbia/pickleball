from FlagEmbedding import FlagModel
from pathlib import Path
import argparse


def load_model(model_path, test="") -> bool:
    try:
        # the model_path is a path to the pytorch.bin file,
        # but the model loading API expects the model directory.
        model_dir = str(Path(model_path).parent)

        sentences = [test]
        model = FlagModel(model_dir)

        embeddings = model.encode(sentences)
        print(embeddings)
        #scores = embeddings @ embeddings.T
        #print(f"Similarity scores:\n{scores}")

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m: {e}")
        print(e)
        return False
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return True


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=(
            "Path to the model (parent directory of pytorch_model.bin)."
        ),
    )
    parser.add_argument(
        "--test",
        default="The happy man has been eating at the diner",
        help=(
            "test input for the model (current string type)"
        ),
    )
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (parent of pytorch_model.bin file) and (optional) test input")
        exit(1)

    load_model(args.model_path, args.test)
