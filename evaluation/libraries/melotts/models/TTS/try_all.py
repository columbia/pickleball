from pathlib import Path
from typing import Iterable, List, Tuple, Optional
import glob, argparse
ALLOWED_PATTERNS = ("checkpoint.pth",)

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

    model_paths = get_model_paths(args.all_model_path)

    count = 0
    from load import load_model
    for model_path in model_paths:
        if(os.path.exists(model_path.replace("checkpoint.pth", "config.json"))):
            load_model(model_path, model_path.replace("checkpoint.pth", "config.json"))
            count += 1
    print(count)
