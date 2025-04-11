import argparse
from pathlib import Path

import torch
from conch.open_clip_custom import create_model_from_pretrained
from PIL import Image
from pklballcheck import collect_attr_stats, verify_loader_was_used

DIR = Path(__file__).parent


def load_model(model_path, test="") -> tuple[bool, str]:
    try:

        model, preprocess = create_model_from_pretrained(
            "conch_ViT-B-16", checkpoint_path=model_path
        )

        image = Image.open(str(DIR / "conch-test" / "test.jpg"))
        image = preprocess(image).unsqueeze(0)
        with torch.inference_mode():
            image_embs = model.encode_image(image, proj_contrast=False, normalize=False)
            print(image_embs)

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False, ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        collect_attr_stats(model)
        return True, image_embs


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=("Path to the model (pytorch_model.bin)."),
    )
    parser.add_argument(
        "--test",
        default="The happy man has been eating at the diner",
        help=("test input for the model (current string type)"),
    )
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (pytorch_model.bin file) and test img input"
        )
        exit(1)

    is_success, output = load_model(args.model_path, args.test)
    print(output)
    verify_loader_was_used()
