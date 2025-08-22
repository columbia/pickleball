#!/usr/bin/env python3

import torch
import glob
import argparse
import time
from pathlib import Path
from typing import List

ALLOWED_PATTERNS = ["*.bin", "*.pkl", "*pt", "*pth"]
EXCLUDED_FILES = ["training_args.bin", "tfevents.bin"]

ITERS = 3


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


model_paths = get_model_paths(
    args.all_model_path,  model_patterns=args.allowed_patterns)
model = model_paths[0]
library = model.split('/')[3]

# Warmup
torch.load(model, map_location=torch.device('cpu'))

times = []

for _ in range(ITERS):
    start = time.time()
    torch.load(model, map_location=torch.device('cpu'))
    end = time.time()
    elapsed = end - start
    times.append(elapsed)

with open(args.output_dir, "a+") as f:
    f.write(f"{library},{pickle_version},{sum(times)/ITERS}")
    f.write("\n")
# print()
