import argparse
import contextlib
import glob
import logging
import sys
from typing import List
from pathlib import Path

import requests

if sys.version_info >= (3, 9):
    from ast import unparse
else:
    from astunparse import unparse

import huggingface_hub

from fickling import tracing
from fickling import fickle
from fickling.pytorch import PyTorchModelWrapper

ALLOWED_PATTERNS = ["*.bin", "*.pth"]

class DummyFile(object):
    def write(self, x): pass


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = save_stdout


def canonical_model_name(model_repo: str) -> str:
    return model_repo.replace('/', '-')


def download(model_repo: str, outdir: str, patterns: List[str] = ALLOWED_PATTERNS, specific_file: bool = False):
    """Downloads models from a Hugging Face repository.

    Specifically fetches models saved with file extensions specified in the
    patterns parameter. For example, to only download models with with ".bin"
    extension, pass the list ["*.bin"] as the patterns parameter.

    Has the effect of saving the downloaded model as a file in the outdir
    directory.
    """

    logging.info('- Downloading models from repo: %s', model_repo)

    if specific_file:
        huggingface_hub.hf_hub_download(
            repo_id=model_repo,
            filename="pytorch_model.bin",
            local_dir=outdir,
            local_dir_use_symlinks=False)
    else:
        huggingface_hub.snapshot_download(
            repo_id=model_repo,
            allow_patterns=patterns,
            local_dir=outdir,
            local_dir_use_symlinks=False)


def generate_stacked_trace(model_path: str) -> str:

    with open(model_path, "rb") as fd:
        try:
            stacked_pickle = fickle.StackedPickle.load(fd)
        except fickle.PickleDecodeError as err:
            logging.error("Pickle load error: %s", err)
            raise RuntimeError(err) from err

    var_id = 0
    trace = ""
    for i, pickled in enumerate(stacked_pickle):
        interpreter = fickle.Interpreter(
            pickled,
            first_variable_id=var_id,
            result_variable=f"result{i}")
        model_trace = tracing.Trace(interpreter)
        with nostdout():
            collected_trace = model_trace.run()
        trace += unparse(collected_trace)
        var_id = interpreter.next_variable_id

    return trace


def generate_trace(model_path: str) -> str:

    pytorch_model = PyTorchModelWrapper(model_path)
    try:
        _ = pytorch_model.formats
    except ValueError as err:
        logging.error("Unable to identify model format: %s", err)
        raise ValueError(err) from err

    interpreter = fickle.Interpreter(
        pytorch_model.pickled,
        first_variable_id=0)
    model_trace = tracing.Trace(interpreter)
    with nostdout():
        collected_trace = model_trace.run()

    return unparse(collected_trace)

def popular_pytorch_repos(n: int = 100):
    """Returns a list of the top n most downloaded Hugging Face repositories.
    """

    api = huggingface_hub.HfApi()
    model_filter = huggingface_hub.ModelFilter(library="pytorch")
    models = api.list_models(
        filter=model_filter,
        sort="downloads",
        direction=-1,
        limit=n)

    return models

def download_and_trace(repository, outdir) -> None:

    # Download any .bin or .pt models in repository.
    try:
        download(repository, outdir)
    except requests.exceptions.HTTPError as err:
        logging.error(err)
    except ConnectionResetError as err:
        logging.error(err)

    # For any .bin or .pt models in the output directory, generate a fickle
    # trace.
    models = []
    for pattern in ALLOWED_PATTERNS:
        glob_pattern = str(outdir / Path(pattern))
        models += glob.glob(glob_pattern)

    for model in models:

        print(f'- Generating trace for model: {model}')
        try:
            trace = generate_trace(model)
        except ValueError:
            print('- Could not trace as PyTorch model. Trying stacked pickle')
            try:
                trace = generate_stacked_trace(model)
            except RuntimeError as err:
                print(f"- Unable to generate trace for model: {model}")
                continue
        finally:
            # Delete the model after tracing
            Path.unlink(Path(model))

        trace_file = model + ".trace"
        print(f"- Writing trace to: {trace_file}")
        with open(trace_file, "w") as fd:
            fd.write(trace)

#def save_repository_metadata(repository: ModelInfo, outdir: Path) -> None:
#    pass

def process_repository(
        repository: str,
        outdir: str,
        _download: bool = True,
        _save_metadata: bool = True,
        _trace: bool = True,
        _delete: bool = True
        ) -> None:

    #if _download:
    #    download_repository_models(repository, outdir)
    #if _save_metadata:
    #    save_repository_metadata(repository, outdir)
    #if _trace:
    #    generate_trace(repository, outdir)
    #if _delete:
    #    delete_models(outdir)

    return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        help="output directory"
        )
    parser.add_argument(
        "--pytorch-only",
        action="store_true",
        default=False,
        help="only download models named 'pytorch_model.bin'")
    parser.add_argument("--repository")
    parser.add_argument("--batch", type=int, default=0)
    parser.add_argument(
        "--download-only",
        action="store_true",
        default=False,
        help="download model without tracing or deleting it")
    parser.add_argument(
        "--batch-process",
        action="store_true",
        default=False,
        help="TODO: set this to automatically download most popular repositories and scan"
    )
    args = parser.parse_args()

    if args.repository:
        if args.outdir:
            outdir: Path = Path(args.outdir) / Path(canonical_model_name(args.repository))
        else:
            outdir: Path = Path.cwd() / Path(canonical_model_name(args.repository))

        if args.download_only:
            download(args.repository, outdir)
        else:
            download_and_trace(args.repository, outdir)
        return

    for repository in popular_pytorch_repos(args.batch):

        logging.info("Repository: %s", repository.id)
        if args.outdir:
            outdir: Path = Path(args.outdir) / Path(canonical_model_name(repository.id))
        else:
            outdir: Path = Path.cwd() / Path(canonical_model_name(repository.id))

        # Only download and trace model if we have not seen this repository
        # before.
        need_to_download = not outdir.exists()
        outdir.mkdir(exist_ok=True)

        logging.info('- Saving repository metadata tags')
        tags_file = outdir / Path(canonical_model_name(repository.id) + '.tags')
        with open(tags_file, "w") as fd:
            fd.write(str(repository.tags))
        name_file = outdir / Path(canonical_model_name(repository.id) + '.name')
        with open(name_file, "w") as fd:
            fd.write(str(repository.id))

        if need_to_download:
            download_and_trace(repository.id, outdir)
        else:
            logging.info("- skipping repository; already analyzed repository: %s", repository.id)


if __name__ == "__main__":
    main()
