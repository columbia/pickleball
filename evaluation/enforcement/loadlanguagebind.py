import argparse
from pathlib import Path

import torch
from languagebind import (
    LanguageBindAudio,
    LanguageBindAudioProcessor,
    LanguageBindAudioTokenizer,
    LanguageBindImage,
    LanguageBindImageProcessor,
    LanguageBindImageTokenizer,
    LanguageBindVideo,
    LanguageBindVideoProcessor,
    LanguageBindVideoTokenizer,
)

from pklballcheck import verify_loader_was_used

def load_model(model_path) -> bool:
   
    model_dir = Path(model_path).parent

    if "AUDIO" in model_dir.name.upper():
        return load_audio_model(str(model_dir))
    elif "IMAGE" in model_dir.name.upper():
        return load_image_model(str(model_dir))
    elif "VIDEO" in model_dir.name.upper():
        return load_video_model(str(model_dir))
    else:
        raise RuntimeError("Unable to identify LanguageBind model type (AUDIO, IMAGE, VIDEO)")


def load_audio_model(model_path) -> bool:
    try:
        model = LanguageBindAudio.from_pretrained(model_path)
        tokenizer = LanguageBindAudioTokenizer.from_pretrained(model_path)
        audio_process = LanguageBindAudioProcessor(model.config, tokenizer)

        model.eval()
        data = audio_process(
            ["assets/audio/0.wav"], ["your audio."], return_tensors="pt"
        )
        with torch.no_grad():
            out = model(**data)

        print(out.text_embeds @ out.image_embeds.T)
    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return True


def load_image_model(model_path):
    try:
        model = LanguageBindImage.from_pretrained(model_path)
        tokenizer = LanguageBindImageTokenizer.from_pretrained(model_path)
        image_process = LanguageBindImageProcessor(model.config, tokenizer)

        model.eval()
        data = image_process(
            ["assets/image/0.jpg"], ["your text."], return_tensors="pt"
        )
        with torch.no_grad():
            out = model(**data)

        print(out.text_embeds @ out.image_embeds.T)
    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return True


def load_video_model(model_path) -> bool:
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
        return False
    else:
        print(f"\033[92mSUCCEEDED in {model_path}\033[0m")
        return True


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path",
        help=("Path to the model (/path/to/parent/of/pytorch_model.bin)."),
    )
    args = parser.parse_args()
    if not args.model_path:
        print(
            "ERROR: need to specify model path (pytorch_model.bin file) and (optional) test input"
        )
        exit(1)

    load_model(args.model_path)
    verify_loader_was_used()
