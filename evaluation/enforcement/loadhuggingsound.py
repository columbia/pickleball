import argparse
from pathlib import Path
from huggingsound import SpeechRecognitionModel

DIR = Path(__file__).parent

def load_model(model_path) -> bool:

    try:
        # the model_path is a path to the pytorch.bin file,
        # but the model loading API expects the model directory.
        model_dir = str(Path(model_path).parent)

        model = SpeechRecognitionModel(model_dir)
        audio_paths = [str(DIR / "test-huggingsound" / "test.wav")]
        transcriptions = model.transcribe(audio_paths)
        print(transcriptions)

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return True


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=(
            "Path to the model (pytorch_model.bin)."
        ),
    )
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (pytorch_model.bin file). test.wav is specified.")
        exit(1)

    load_model(args.model_path)
