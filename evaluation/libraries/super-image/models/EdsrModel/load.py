from super_image import EdsrModel, ImageLoader
from PIL import Image
import argparse


def load_model(model_path, original_image=""):
    image = Image.open(original_image)
    try:

        for s in [2,3,4]:
            model = EdsrModel.from_pretrained(model_path, scale=s)      # scale 2, 3 and 4 models available
            inputs = ImageLoader.load_image(image)
            preds = model(inputs)
            print(preds)

            #ImageLoader.save_image(preds, './scaled_2x.png')                        # save the output 2x scaled image to `./scaled_2x.png`
            #ImageLoader.save_compare(inputs, preds, './scaled_2x_compare.png')      # save an output comparing the super-image with a bicubic scaling
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
            "Path to the model (pytorch_model.bin)."
        ),
    )
    parser.add_argument(
        "--test",
        default="test.png",
        help=(
            "test image for the model"
        ),
    )

    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (parent directory of pytorch_model.bin file) and test image")
        exit(1)

    load_model(args.model_path, args.test)
