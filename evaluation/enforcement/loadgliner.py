import argparse
from gliner import GLiNER
from pathlib import Path

from pklballcheck import verify_loader_was_used

#model = GLiNER.from_pretrained("EmergentMethods/gliner_medium_news-v2.1")
#model = GLiNER.from_pretrained("/data/no-malicious/gliner/GliNER/DeepMount00-GLiNER_ITA_BASE",

TEXT = """
The Chihuahua State Public Security Secretariat (SSPE) arrested 35-year-old Salomón C. T. in Ciudad Juárez, found in possession of a stolen vehicle, a white GMC Yukon, which was reported stolen in the city's streets. The arrest was made by intelligence and police analysis personnel during an investigation in the border city. The arrest is related to a previous detention on February 6, which involved armed men in a private vehicle. The detainee and the vehicle were turned over to the Chihuahua State Attorney General's Office for further investigation into the case.
"""

LABELS = ["person", "location", "date", "event", "facility", "vehicle", "number", "organization"]

def load_model(model_path, text=TEXT, labels=LABELS) -> bool:
    try:
        # the model_path is a path to the pytorch.bin file,
        # but the model loading API expects the model directory.
        model_dir = str(Path(model_path).parent)

        model = GLiNER.from_pretrained(model_dir, local_files_only=True)
        entities = model.predict_entities(text, labels)

        for entity in entities:
            print(entity["text"], "=>", entity["label"])
        
    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m: {e}")
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
            "Path to the model directory (pytorch_model.bin)."
        ),
    )
    parser.add_argument(
        "--test",
        default="The happy man has been eating at the diner",
        help=(
            "test input for the model (current string type)"
        ),
    )
    args = parser.parse_args()
    if not args.model_path:
        print("ERROR: need to specify model directory (pytorch_model.bin) and (optional) test input")
        exit(1)

    load_model(args.model_path, args.test)
    if verify_loader_was_used():
        print("Loader used")
    else:
        print("Error: Loader not used")
