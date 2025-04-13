#!/usr/bin/env python3

import argparse
import glob
import importlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from pklballcheck import verify_loader_was_used

DIR = Path(__file__).parent
ALLOWED_PATTERNS = ["*.bin", "*.pkl", "*pt", "*pth"]
EXCLUDED_FILES = ["training_args.bin", "tfevents.bin"]

LIBRARIES = [
    "conch",
    "flair",
    "flagembedding",
    "gliner",
    "huggingsound",
    "languagebind",
    "melotts",
    "parrot",
    "pyannote",
    "pysentimiento",
    "sentencetransformers",
    "superimage",
    "tner",
    "tweetnlp",
    "yolov5",
    "yolov11"
]


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


if __name__ == "__main__":
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all-model-path",
        default="/load-model/models",
        help=("the location of all models to test"),
    )
    parser.add_argument("--library", help="name of library to evaluate")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run model with a big dataset for validation",
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
    parser.add_argument(
        "--disable-verify",
        help=(
            "Disable verification that pickleball loader was used to load "
            "libraries. If not set, a test fails if the loader is not "
            "detected. This can be set if the loader is used without "
            "pickleball."
        ),
        action="store_true",
    )
    parser.add_argument(
        "--output-dir",
        help=("Path to write output log file, relative to this file path"),
        type=Path,
    )

    args = parser.parse_args()
    if not args.all_model_path or not args.library:
        print("ERROR: need to specify model path and library")
        exit(1)

    if args.library not in LIBRARIES:
        print("ERROR: invalid library name")
        exit(1)

    LIBRARY = args.library
    module_name = f"load{args.library}"

    try:
        loading_module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        print(f"ERROR: Module {module_name} not found.")
        exit(1)

    if not args.output_dir:
        LOG = DIR / "results" / f"{LIBRARY}.log"
    else:
        LOG = args.output_dir / f"{LIBRARY}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(str(LOG), mode="w")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logging.info(f"loading all {LIBRARY} libraries")
    logging.info(f"writing log to {str(LOG)}")
    logging.info(f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"models: {args.all_model_path}")
    logging.info(f"load function: {module_name}.load_model")

    model_paths = get_model_paths(
        args.all_model_path, model_patterns=args.allowed_patterns
    )
    logging.info(f"# models: {len(model_paths)}")

    successes = 0
    for model_path in model_paths:
        logging.debug(f"loading model: {model_path}")
        if args.validate:
            output = loading_module.validate_model(model_path)
            logging.info(f"{model_path} OUTPUT:")
            logging.info(output)
        else:
            start_time = time.time()
            is_success, output = loading_module.load_model(model_path)
            end_time = time.time()
            logging.info(f"TIME,{end_time - start_time}")
            if len(output) == 0:
                logging.warn(f"WARNING: Empty output for {model_path}")
            loader_used = verify_loader_was_used() or args.disable_verify
            if is_success and loader_used:
                logging.info(f"{model_path} SUCCESS")
                logging.info(f"{model_path} OUTPUT:")
                logging.info(output)
                successes += 1
            else:
                if not loader_used:
                    logging.error(
                        f"ERROR: pickleball loader was not used for {model_path}"
                    )
                logging.info(f"{model_path} FAILURE")

        logging.info(f"{successes}:{len(model_paths)}")
