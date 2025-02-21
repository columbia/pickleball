from FlagEmbedding import FlagModel
import argparse



def load_model(model_path, test=""):
    try:
        sentences = [test]
        model = FlagModel(model_path)

        embeddings = model.encode(sentences)
        print(embeddings)
        #scores = embeddings @ embeddings.T
        #print(f"Similarity scores:\n{scores}")

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m: {e}")
        print(e)
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")



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
