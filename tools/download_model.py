import argparse
from pathlib import Path

import huggingface_hub

REPO = "Supabase/gte-small"
ALLOWED_PATTERNS = ["*.bin", "*.pth"]

def download(model: str, parent_outdir: str = None, specific_file: bool = False):

    if parent_outdir:
        outdir: Path = Path(parent_outdir) / Path(model.replace('/', '-'))
    else:
        outdir: Path = Path.cwd() / Path(model.replace('/', '-'))
    outdir.mkdir(exist_ok=True)

    if specific_file:
        huggingface_hub.hf_hub_download(
            repo_id=model,
            filename="pytorch_model.bin",
            local_dir=outdir,
            local_dir_use_symlinks=False)
    else:
        huggingface_hub.snapshot_download(
            repo_id=model,
            allow_patterns=ALLOWED_PATTERNS,
            local_dir=outdir,
            local_dir_use_symlinks=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "repository",
        help="name of the HuggingFace repository to fetch pickle models from")
    parser.add_argument(
        "--outdir",
        help="output directory"
        )
    parser.add_argument(
        "--pytorch-only",
        action="store_true",
        default=False,
        help="only download models named 'pytorch_model.bin'")
    args = parser.parse_args()

    download(args.repository, args.outdir, args.pytorch_only)
