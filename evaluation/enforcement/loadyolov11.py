import argparse
from pathlib import Path

import ultralytics

#from pklballcheck import collect_attr_stats, verify_loader_was_used
from pklballcheck import verify_loader_was_used

#IMG_PATH = 'https://github.com/ultralytics/yolov5/raw/master/data/images/zidane.jpg'
DIR = Path(__file__).parent
IMG_PATH = DIR / Path('test-yolov11') / Path('zidane.jpg')


def load_model(model_path, test=IMG_PATH) -> bool:

    try:
        model = ultralytics.YOLO(model_path)
        results = model.predict(test, save=False)

        print(f'results: {results}')

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False, ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        #collect_attr_stats(model)
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
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (.pt file) and (optional) "
              "test input")
        exit(1)

    load_model(args.model_path, args.test)
    verify_loader_was_used()
