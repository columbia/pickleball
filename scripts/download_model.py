"""
Script for downloading PyTorch models from HuggingFace, and generating a
fickling trace of each model.

Can be run on specifically identified repositories (--repository
<namespace/repo>), a list of repositories (--repositories-list <file>) or as a
batch process over the n most downloaded HuggingFace repositories with PyTorch
models (--batch n).

To run this script, you must first authenticate with the Hugging Face API:
    `$ huggingface-cli login`

    (see: https://huggingface.co/docs/huggingface_hub/quick-start#authentication)

"""

import argparse
import contextlib
import glob
import logging
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

import requests

if sys.version_info >= (3, 9):
    from ast import unparse
else:
    from astunparse import unparse

import huggingface_hub
import huggingface_hub.hf_api
from fickling import fickle, tracing
from fickling.pytorch import PyTorchModelWrapper

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Default set of file extensions that represent PyTorch models. Not every .bin
# model will be a PyTorch model, and other PyTorch model file extensions may
# exist.
ALLOWED_PATTERNS = ("*.bin", "*.pth", "*.pt")


# The fickling module generates a lot of printed output statements when tracing
# a pickle program. I use this dummy file and context manager to silence the
# output statements to avoid cluttering stdout.
class DummyFile(object):
    def __init__(self, filename=None):
        self.filename = filename
        if filename:
            self.file = open(filename, 'a')
        else:
            self.file = None

    def write(self, x):
        if self.file:
            self.file.write(x)

    def flush(self):
        if self.file:
            self.file.flush()

    def close(self):
        if self.file:
            self.file.close()


# Used to prevent cluttering stdout when generating fickling trace. See comment
# above DummyFile.
@contextlib.contextmanager
def nostdout(opcode_filename=None):
    save_stdout = sys.stdout
    dummy_file = DummyFile(opcode_filename)
    sys.stdout = dummy_file
    yield
    sys.stdout = save_stdout
    dummy_file.close()


def canonical_model_name(model_repo: str) -> str:
    """HuggingFace repositories are identified in the form of
    'namespace/repository'.
    For saving the repository contents, convert the '/'
    in the name to a '-' in the output directory name to avoid creating
    subdirectories.
    """
    return model_repo.replace("/", "-")


def download(
    model_repo: str,
    outdir: Path,
    patterns: Tuple[str] = ALLOWED_PATTERNS,
    specific_file: bool = False,
):
    """Downloads models from a Hugging Face repository.

    Specifically fetches models saved with file extensions specified in the
    patterns parameter. For example, to only download models with with ".bin"
    extension, pass the list ["*.bin"] as the patterns parameter.

    Has the effect of saving the downloaded model as a file in the outdir
    directory.

    TODO:
        - Indicate that a download error occurred.
        - Specify exactly which file to download from a repository without
          hardcoding.
    """

    logging.info("- Downloading models from repo: %s", model_repo)

    if specific_file:
        try:
            huggingface_hub.hf_hub_download(
                repo_id=model_repo,
                filename="pytorch_model.bin",
                local_dir=str(outdir),
                local_dir_use_symlinks=True,
                cache_dir=str(outdir / Path(".cache")),
            )
        except requests.exceptions.HTTPError as err:
            logging.error(err)
        except ConnectionResetError as err:
            logging.error(err)

    else:
        try:
            huggingface_hub.snapshot_download(
                repo_id=model_repo,
                allow_patterns=patterns,
                local_dir=str(outdir),
                local_dir_use_symlinks=True,
                cache_dir=str(outdir / Path(".cache")),
            )
        except requests.exceptions.HTTPError as err:
            logging.error(err)
        except ConnectionResetError as err:
            logging.error(err)


def _generate_stacked_trace(model_path: str, write_opcode: bool) -> str:

    with open(model_path, "rb") as fd:
        try:
            stacked_pickle = fickle.StackedPickle.load(fd)
        except fickle.PickleDecodeError as err:
            logging.error("Pickle load error: %s", err)
            raise RuntimeError(err) from err

    var_id = 0
    trace = ""
    opcode_filename = model_path + ".opcode" if write_opcode else None
    for i, pickled in enumerate(stacked_pickle):
        interpreter = fickle.Interpreter(
            pickled, first_variable_id=var_id, result_variable=f"result{i}"
        )
        model_trace = tracing.Trace(interpreter)
        with nostdout(opcode_filename):
            collected_trace = model_trace.run()
        trace += unparse(collected_trace)
        var_id = interpreter.next_variable_id

    return trace


def _generate_pytorch_trace(model_path: str, write_opcode: bool) -> str:

    pytorch_model = PyTorchModelWrapper(model_path)
    try:
        _ = pytorch_model.formats
    except ValueError as err:
        logging.error("Unable to identify model format: %s", err)
        raise ValueError(err) from err

    interpreter = fickle.Interpreter(pytorch_model.pickled, first_variable_id=0)
    model_trace = tracing.Trace(interpreter)
    opcode_filename = model_path + ".opcode" if write_opcode else None
    with nostdout(opcode_filename):
        collected_trace = model_trace.run()

    return unparse(collected_trace)


def generate_trace(model_path: str, delete_after_tracing: bool = True, write_opcode: bool = False) -> str:
    """Generate a trace of a PyTorch model using the fickling library."""

    logging.info("Generating trace for model: %s", model_path)
    trace = ""
    # TODO: Tidy this up. Currently, the code tries to first use the fickling
    # PyTorchWrapper API to interact with the model, but this may fail when the
    # model is a 'stacked' pickle file, in which case I use the StackedPickle
    # API. I should be able to test ahead of time for the model type and then
    # select the right approach.
    try:
        trace = _generate_pytorch_trace(model_path, write_opcode)
    except ValueError:
        logging.warning("- Could not trace as PyTorch model. Trying stacked pickle")
        try:
            trace = _generate_stacked_trace(model_path, write_opcode)
        except RuntimeError as err:
            logging.warning("- Unable to generate trace for model: %s", model_path)
            logging.warning("%s", err)
    finally:
        if delete_after_tracing:
            Path.unlink(Path(model_path))

    # First check if a trace was generated before attempting to write it out.
    if trace:
        trace_file = model_path + ".trace"
        logging.info("- Writing trace to: %s", trace_file)
        with open(trace_file, "w") as fd:
            fd.write(trace)


def popular_repos(n: int = 100, lib: str = "pytorch") -> Iterable[huggingface_hub.hf_api.ModelInfo]:
    """Returns iterable of the top n most downloaded Hugging Face repositories,
    sorted from most downloaded to least downloaded.
    """

    api = huggingface_hub.HfApi()
    model_filter = huggingface_hub.ModelFilter(library=lib)
    models = api.list_models(
        filter=model_filter, sort="downloads", direction=-1, limit=n
    )

    return models


def get_model_info(repository: str) -> huggingface_hub.hf_api.ModelInfo:
    """Given a repository name, fetch the model info metadata from HuggingFace."""
    return huggingface_hub.HfApi().model_info(repository)


def save_repository_metadata(
    model_info: huggingface_hub.hf_api.ModelInfo, outdir: Path
) -> None:
    """Given a HuggingFace ModelInfo object, save metadata to files in the
    output directory.

    Metadata saved:
    - name
    - tags
    """

    logging.info("Saving repository metadata: %s", model_info.id)

    tags_file = outdir / Path(canonical_model_name(model_info.id) + ".tags")
    with open(tags_file, "w") as fd:
        fd.write(str(model_info.tags))

    name_file = outdir / Path(canonical_model_name(model_info.id) + ".name")
    with open(name_file, "w") as fd:
        fd.write(str(model_info.id))


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


def process_repository(
    model_info: huggingface_hub.hf_api.ModelInfo,
    repo_outdir: Path,
    force_download: bool = False,
    save_metadata: bool = True,
    trace: bool = True,
    delete_after_processing: bool = True,
    write_opcode: bool = False,
) -> None:
    """Process a Hugging Face repository. Defaults behavior is to:
     1. save metadata about the repository
     2. download the select models from the repository
     3. generate a fickling trace of the downloaded models
     4. delete the downloaded models

    Any of these processing steps can be skipped by toggling the associated
    boolean parameter to this function.

    TODO: Describe the output directory naming convention.
    TODO: Allow user to set patterns for model extensions.
    """

    need_to_download = force_download or not repo_outdir.exists()
    repo_outdir.mkdir(exist_ok=True)

    if not need_to_download:
        logging.warning("skipping download of repository: %s", model_info.id)
    else:
        if save_metadata:
            save_repository_metadata(model_info, repo_outdir)
        download(model_info.id, repo_outdir)

    if trace:
        model_paths = get_model_paths(repo_outdir)
        for model_path in model_paths:
            generate_trace(model_path, delete_after_processing, write_opcode)
        if delete_after_processing:
            # Remove cached model directory (automatically created by
            # HuggingFace when downloading).
            shutil.rmtree(repo_outdir / Path(".cache"), ignore_errors=True)


def main():
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        help=(
            "Output parent directory where the processed model will be saved. "
            "If not set, the current directory will be used."
        ),
    )
    parser.add_argument(
        "--repository",
        help=(
            "Name of HuggingFace repository to process, in form of "
            "'namespace/repository'"
        ),
    )
    parser.add_argument(
        "--repositories-list",
        help=(
            "Filename containing a list of line separated HuggingFace"
            "repositories to process, in form of 'namespace/repository'"
        ),
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=0,
        help="Number of repositories to batch process (if --repository not set).",
    )
    parser.add_argument(
        "--library",
        type=str,
        help="The library to download (if --batch is set).",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        default=False,
        help=(
            "Force download the model while processing. If this is not set, "
            "the model will not be downloaded when the repository output "
            "directory already exists."
        ),
    )
    parser.add_argument(
        "--write-opcode",
        action="store_true",
        default=False,
        help=(
            "Write down the printed opcode into file, if set"
        ),
    )
    parser.add_argument(
        "--no-trace",
        action="store_true",
        default=False,
        help=(
            "Do not trace the downloaded model. If this is not set, the "
            "model will be traced after downloading."
        ),
    )
    parser.add_argument(
        "--no-delete",
        action="store_true",
        default=False,
        help=(
            "Do not delete the model after processing it. If this is not "
            "set, the downloaded model will be deleted."
        ),
    )
    args = parser.parse_args()

    if args.repository:
        repositories = []
        try:
            for repo in args.repository.split(','):
                repositories.append(get_model_info(repo))
        except huggingface_hub.utils._errors.RepositoryNotFoundError as err:
            logging.error(err)
            return

    elif args.repositories_list:
        repositories_list = []
        with open(args.repositories_list, 'r') as fd:
            for line in fd:
                repositories_list.append(line.strip())

        try:
            repositories = [get_model_info(repository) for repository in repositories_list]
        except huggingface_hub.errors.RepositoryNotFoundError as err:
            logging.error(err)
            return

    elif args.batch > 0:
        repositories = popular_repos(args.batch, args.library)
    else:
        logging.error(
            "need to either specify a repository to process with the "
            "'--repository' argument, '--repositories-list' argument, or the "
            "number of repositories to batch process with the --batch argument"
        )
        return

    if args.outdir:
        outdir: Path = Path(args.outdir)
    else:
        outdir: Path = Path.cwd()
    outdir.mkdir(exist_ok=True)

    for repository in repositories:
        process_repository(
            repository,
            outdir / Path(canonical_model_name(repository.id)),
            force_download=args.force_download,
            save_metadata=True,
            trace=not args.no_trace,
            delete_after_processing=not args.no_delete,
            write_opcode= args.write_opcode
        )


if __name__ == "__main__":
    main()

