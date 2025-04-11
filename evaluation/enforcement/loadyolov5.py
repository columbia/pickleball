import argparse

import yolov5

#from pklballcheck import collect_attr_stats, verify_loader_was_used
from pklballcheck import verify_loader_was_used

#TEST = "I love berlin."
IMG_PATH = 'https://github.com/ultralytics/yolov5/raw/master/data/images/zidane.jpg'

def load_model(model_path, test=IMG_PATH) -> tuple[bool, str]:

    try:
        model = yolov5.load(model_path)
        results = model(test)

        predictions = results.pred[0]

        print(f'predictions: {predictions}')

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False, ""
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        print(type(model))
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
