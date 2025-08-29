"""Given a path to a pickle file, output a torch model that includes the
pickle program.
"""

import argparse
from pathlib import Path
import zipfile

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Turn a pickle program into a PyTorch-structured model")
    parser.add_argument(
        'pickle',
        type=Path,
        help='Path to pickle program')

    parser.add_argument(
        'data',
        type=Path,
        default=Path('dummy-archive'),
        help='Path to dummy archive data to write to the model'
    )

    args = parser.parse_args()

    with zipfile.ZipFile('pytorch_model.bin', 'w') as zipf:
        zipf.write(args.pickle, Path("archive") / "data.pkl")

        for file_path in args.data.rglob('*'):
            if file_path.is_file():
                archive_path = Path("archive") / file_path.relative_to(args.data)
                zipf.write(file_path, archive_path)
