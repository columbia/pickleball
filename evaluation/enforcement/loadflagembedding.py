import argparse
import traceback
from pathlib import Path

from FlagEmbedding import FlagModel
from pklballcheck import collect_attr_stats

TEST = "The experienced professor from Harvard University quickly analyzed the ancient manuscript while drinking coffee in New York last Sunday."
sentences_1 = ["样例数据-1", "样例数据-2"]
sentences_2 = ["样例数据-3", "样例数据-4"]


def load_model(model_path, test=TEST) -> tuple[bool, str]:
    model = None
    try:
        # the model_path is a path to the pytorch.bin file,
        # but the model loading API expects the model directory.
        model_dir = str(Path(model_path).parent)

        sentences = [test]
        # model = FlagModel(model_dir)
        model = FlagModel(
            model_dir,
            query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
        )
        # use_fp16=True)

        embeddings = model.encode(sentences)
        # print(embeddings)
        # scores = embeddings @ embeddings.T
        # print(f"Similarity scores:\n{scores}")

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m: {e}")
        print(e)
        stack_trace = traceback.format_exc()
        print(stack_trace)
        return False, ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        # collect_attr_stats(model)
        return True, embeddings


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=("Path to the model (parent directory of pytorch_model.bin)."),
    )
    parser.add_argument(
        "--test",
        default="The happy man has been eating at the diner",
        help=("test input for the model (current string type)"),
    )
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (parent of pytorch_model.bin file) and (optional) test input"
        )
        exit(1)

    is_success, output = load_model(args.model_path, args.test)
    print(output)
