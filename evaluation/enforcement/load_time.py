#!/usr/bin/env python3

import argparse
import glob
import pickle
import sys
import time
from pathlib import Path
from typing import List

import torch

ALLOWED_PATTERNS = ["*.bin", "*.pkl", "*pt", "*pth"]
EXCLUDED_FILES = ["training_args.bin", "tfevents.bin"]
CURRENT_LIBRARY = ""
OUTPUT_DIR = "/results/times.csv"
MODELS_TESTED = "/results/models.txt"

WARMUP_ITERS = 3
ITERS = 10
WARMUP = True

original_load = pickle._Unpickler.load


def hooked_load(self, *args, **kwargs):
    start_time = time.time()
    ret = original_load(self, *args, **kwargs)
    end_time = time.time()
    elapsed = end_time - start_time
    if not WARMUP:
        with open(OUTPUT_DIR, "a+") as f:
            f.write(f"{CURRENT_LIBRARY},{pickle_version},{elapsed}")
            f.write("\n")
    return ret


pickle._Unpickler.load = hooked_load


def get_model_paths(
    directory: Path, model_patterns: List[str] = ALLOWED_PATTERNS
) -> List[str]:
    """Given a directory that contains downloaded models and a list of file
    extensions of models, return a list of paths to all models found in the
    directory.

    When model_patterns = None, the ALLOWED_PATTERNS default list is used.
    """

    models = []
    for pattern in model_patterns:
        glob_pattern = str(directory / Path("**") / Path(pattern))
        models += glob.glob(glob_pattern)

    # Remove any matched files that should not be included
    return [model for model in models if Path(model).name not in EXCLUDED_FILES]


parser = argparse.ArgumentParser()
parser.add_argument(
    "--all-model-path",
    default="/load-model/models",
)
parser.add_argument(
    "--output-dir",
    type=Path,
)
parser.add_argument(
    "--allowed-patterns",
    nargs="*",
    help=(
        "A list of patterns indicating a model of this type. If none "
        "are provided, defaults to ALLOWED_PATTERNS"
    ),
    default=ALLOWED_PATTERNS,
)
args = parser.parse_args()


# Check which pickle loader we are using by trying to import something that only
# exists in the PickleBall version of the loader
pickle_version = "vanilla"
try:
    from pickle import POLICY_PATH

    pickle_version = "pickleball"
except:
    pass


model_paths = get_model_paths(args.all_model_path, model_patterns=args.allowed_patterns)
if len(model_paths) == 0:
    print("No models found")
    sys.exit(1)

model = model_paths[0]
library = model.split("/")[3]


# yolov5 models assume yolov5 is already loaded
if library == "yolov5":
    import yolov5

    # ensure that we select a yolov5 model that loads with PB policies
    model = "/models/benign/yolov5/keremberke-yolov5m-smoke/best.pt"
# ensure that we select a yolov11 model that loads with PB policies
if library == "yolov11":
    model = "/models/benign/yolov11/Anzhc-Anzhcs_YOLOs/Anzhcs ManFace v02 1024 y8n.pt"
# ensure that we select a pyannote model that loads with PB policies
if library == "pyannote-audio":
    model = "/models/benign/pyannote-audio/Model/pyannote-wespeaker-voxceleb-resnet34-LM/pytorch_model.bin"
# ensure that we select a flair model that loads with PB policies
if library == "flair":
    model = (
        "/models/benign/flair/SequenceTagger/flair-upos-english-fast/pytorch_model.bin"
    )

CURRENT_LIBRARY = library

print(f"Attempting to load model: {model}")
with open(MODELS_TESTED, "a+") as f:
    f.write(f"{model}\n")

# Warmup
for _ in range(WARMUP_ITERS):
    torch.load(model, map_location=torch.device("cpu"))

WARMUP = False

for _ in range(ITERS):
    torch.load(model, map_location=torch.device("cpu"))

# print()
