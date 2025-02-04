from melo.api import TTS
from pklballcheck import verify_loader_was_used
import argparse
# https://github.com/myshell-ai/MeloTTS/blob/5b538481e24e0d578955be32a95d88fcbde26dc8/melo/download_utils.py#L33C1-L33C19
LANG_MAP = {
    'MeloTTS-English':'EN',
    'MeloTTS-English-v2':'EN_V2',
    'MeloTTS-English-v3':'EN_NEWEST',
    'MeloTTS-French':'FR',
    'MeloTTS-Japanese':'JP',
    'MeloTTS-Spanish':'ES',
    'MeloTTS-Chinese':'ZH',
    'MeloTTS-Korean':'KR',
}

def load_model(model_path, model_config, text="Hello World"):

    if True:
        repo = model_path.split("/")[-2]
        print(repo)
        model_language = "-".join(repo.split("-")[2:])
        model_language = LANG_MAP[model_language]


        model = TTS(language=model_language, use_hf=False, device="cpu", config_path=model_config, ckpt_path=model_path)
        speaker_ids = model.hps.data.spk2id
        speakers = list(speaker_ids.keys())
        output_path = 'test.wav'
        for speaker in speakers:
            model.tts_to_file(text, speaker_ids[speaker], output_path, speed=1.0)

            # just one is enough
            break
    try:
        pass


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
            "Path to the model (checkpoint.pth)."
        ),
    )
    parser.add_argument(
        "--config-path",
        help=(
            "Path to the config (config.json)."
        ),
    )
    parser.add_argument(
        "--test",
        default="The happy man has been eating at the diner",
        help=(
            "test input for the model"
        ),
    )
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model path (checkpoint.pth), cofig path, and test input")
        exit(1)

    load_model(args.model_path, args.config_path, args.test)
    verify_loader_was_used()
