import argparse
import traceback
from pathlib import Path

# from pklballcheck import verify_loader_was_used
from PIL import Image
from pklballcheck import collect_attr_stats, verify_loader_was_used
from super_image import EdsrModel, ImageLoader

DIR = Path(__file__).parent


def load_model(model_path) -> tuple[bool, str]:

    test_image = DIR / "test-superimage" / "test.png"
    image = Image.open(str(test_image))
    inputs = ImageLoader.load_image(image)

    model_dir = Path(model_path).parent

    try:
        # for s in [2,3,4]:
        model = EdsrModel.from_pretrained(
            str(model_dir), scale=2
        )  # scale 2, 3 and 4 models available
        preds = model(inputs)
        # print(preds)

        # ImageLoader.save_image(preds, './scaled_2x.png')                        # save the output 2x scaled image to `./scaled_2x.png`
        # ImageLoader.save_compare(inputs, preds, './scaled_2x_compare.png')      # save an output comparing the super-image with a bicubic scaling
    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        stack_trace = traceback.format_exc()
        print(stack_trace)
        return False, ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        collect_attr_stats(model)
        return True, preds


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=("Path to the model (pytorch_model.bin)."),
    )
    parser.add_argument(
        "--test",
        default="test.png",
        help=("test image for the model"),
    )

    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (parent directory of pytorch_model.bin file) and test image"
        )
        exit(1)

    is_success, output = load_model(args.model_path)
    print(output)
#    verify_loader_was_used()
