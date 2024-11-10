import argparse
from pyannote.audio import Pipeline

def load_model(model_path):
    try:
        pipeline = Pipeline.from_pretrained(model_path)
        #audio_in_memory = {"waveform": waveform, "sample_rate": sample_rate}
        dia = pipeline("sample.wav")
        print(f"Annotation contains {len(dia)} speech segments, covering a total duration of {dia.get_timeline().duration()} seconds.")

    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=(
            "Path to the model (modified config.yaml)."
            "https://github.com/pyannote/pyannote-audio/blob/develop/tutorials/applying_a_pipeline.ipynb"
        ),
    )
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (pytorch_model.bin file). No test is needed.")
        exit(1)

    load_model(args.model_path)
