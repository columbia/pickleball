import argparse
from pklballcheck import verify_loader_was_used

import torch
from languagebind import (
    LanguageBindVideo,
    LanguageBindVideoProcessor,
    LanguageBindVideoTokenizer,
)


def load_model(model_path, test=""):
    try:
        model = LanguageBindVideo.from_pretrained(model_path)
        tokenizer = LanguageBindVideoTokenizer.from_pretrained(model_path)
        video_process = LanguageBindVideoProcessor(model.config, tokenizer)

        model.eval()
        data = video_process(
            ["assets/video/0.mp4"], ["your text."], return_tensors="pt"
        )
        with torch.no_grad():
            out = model(**data)

        print(out.text_embeds @ out.image_embeds.T)
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
        help=("Path to the model (/path/to/parent/of/pytorch_model.bin)."),
    )
    parser.add_argument(
        "--test",
        default="The happy man has been eating at the diner",
        help=("test input for the model (current string type)"),
    )
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (pytorch_model.bin file) and (optional) test input"
        )
        exit(1)

    load_model(args.model_path, args.test)
    verify_loader_was_used()
