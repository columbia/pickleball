#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple, Optional
import argparse
import glob
import logging

import loadflair

LOADS = {
    'flair': loadflair.load_model,
}

LIBRARY = 'flair'

DIR = Path(__file__).parent
LOG = DIR / "results" / f"{LIBRARY}.log"

ALLOWED_PATTERNS = ("*.bin", "*.pkl", "*pt", "*pth")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(str(LOG), mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(message)s'))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(logging.Formatter('%(message)s'))

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def get_model_paths(
    directory: Path, model_patterns: Tuple[str] = ALLOWED_PATTERNS
) -> List[str]:
    """Given a directory that contains downloaded models and a list of file
    extensions of models, return a list of paths to all models found in the
    directory.

    When model_patterns = None, the ALLOWED_PATTERNS default list is used.
    """

    models = []
    for pattern in model_patterns:
        glob_pattern = str(directory / Path('**') / Path(pattern))
        models += glob.glob(glob_pattern, recursive=True)
    return models


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all-model-path",
        default="/load-model/models",
        help=(
            "the location of all models to test"
        ),
    )

    args = parser.parse_args()
    if not args.all_model_path:
        print("ERROR: need to specify model path")

    logging.info(f"loading all {LIBRARY} libraries")
    logging.info(f"writing log to {str(LOG)}")
    logging.info(f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"models: {args.all_model_path}")

    model_paths = get_model_paths(args.all_model_path)
    logging.info(f"# models: {len(model_paths)}")

    successes = 0
    for model_path in model_paths:
        logging.debug(f"loading model: {model_path}")
        if LOADS[LIBRARY](model_path):
            logging.info(f"{model_path} SUCCESS")
            successes += 1
        else:
            logging.info(f"{model_path} FAILURE")

    logging.info(f"{successes}:{len(model_paths)}")

