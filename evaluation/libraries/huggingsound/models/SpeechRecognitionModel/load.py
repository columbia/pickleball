import argparse
from huggingsound import SpeechRecognitionModel

def load_model(model_path):

    try:
        model = SpeechRecognitionModel(model_path)
        audio_paths = ["test.wav"]
        transcriptions = model.transcribe(audio_paths)
        print(transcriptions)

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
            "Path to the model (parent of pytorch_model.bin)."
        ),
    )
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (parent of pytorch_model.bin file). test.wav is specified.")
        exit(1)

    load_model(args.model_path)
