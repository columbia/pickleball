import argparse
import os
from pathlib import Path

import ultralytics

# from pklballcheck import collect_attr_stats, verify_loader_was_used
try:
    from pklballcheck import verify_loader_was_used
except:
    pass

# IMG_PATH = 'https://github.com/ultralytics/yolov5/raw/master/data/images/zidane.jpg'
DIR = Path(__file__).parent
IMG_PATH = DIR / Path("test-yolov11") / Path("zidane.jpg")
VALIDATION_DIR = Path("/datasets/yolo/test2017")


def validate_model(model_path) -> str:

    validation_files = os.listdir(VALIDATION_DIR)
    validation_files.sort()

    try:
        model = ultralytics.YOLO(model_path)

        all_output = ""
        for file in validation_files[:100]:
            results = model.predict(VALIDATION_DIR / file, save=False)
            output = "\n".join([str(x.boxes) for x in results])
            all_output += output
            # print(results)

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return all_output


def load_model(model_path, test=IMG_PATH) -> tuple[bool, str]:

    try:
        model = ultralytics.YOLO(model_path)
        results = model.predict(test, save=False)

        print(f"results: {results}")

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False, ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        # collect_attr_stats(model)
        return True, str(results)


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=("Path to the model (best.pt)."),
    )
    parser.add_argument(
        "--test",
        default=IMG_PATH,
        help=("Path to an image to test."),
    )
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (.pt file) and (optional) " "test input"
        )
        exit(1)

    if args.validate:
        output = validate_model(args.model_path)
        print(output)
    else:
        is_success, output = load_model(args.model_path)
        print(output)
    verify_loader_was_used()
