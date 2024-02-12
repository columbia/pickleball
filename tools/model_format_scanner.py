"""
Matches files in a given directory with their corresponding DL model format.
Warning: For a lot of the formats we try to actually load the model, which
might be dangerous since some formats are vulnerable
Requires:
    - colorlog
    - paddlepaddle
    - safetensors
    - torch
    - tensorflow
    - onnx
    - flax
    - coremltools
    - numpy
    - mleap
"""
import argparse
import logging
import os
import pdb
import sys
from pickletools import dis as pickle_dis

import colorlog
from coremltools.models import MLModel as coreml_load
from flax.serialization import msgpack_restore as flax_msgpack_restore

# from mleap.combust.bundle import BundleFile as mleap_load
from numpy import load as numpy_load
from onnx import load as onnx_load
from orbax.checkpoint import PyTreeCheckpointer
from paddle import load as paddle_load
from safetensors import safe_open as safetensors_open
from tensorflow.keras.models import load_model as keras_load
from tensorflow.saved_model import load as tf_saved_model_load
from torch import load as torch_load
from torch.jit import load as torchscript_load

logger = logging.getLogger(__name__)

formatter = colorlog.ColoredFormatter(
    "%(log_color)s[%(levelname)s]: %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
    },
)


class ModelFormat:
    def __str__(self):
        return "ModelFormat"

    def matches(self, filename):
        return False


class Pickle(ModelFormat):
    expected_suffixes = ["pkl"]

    def __str__(self):
        return "Pickle"

    def matches(self, filename):
        with open(os.devnull, "w") as devnull:
            try:
                with open(filename, "rb") as file:
                    pickle_dis(file, out=devnull)
                return True
            except Exception as e:
                # print(filename, e)
                return False


class TorchScript(ModelFormat):
    expected_suffixes = ["pt", "pth"]

    def __str__(self):
        return "TorchScript"

    def matches(self, filename):
        try:
            torchscript_load(filename)
            return True
        except Exception as e:
            # print(filename, e)
            return False


class TorchSave(ModelFormat):
    expected_suffixes = ["bin"]

    def __str__(self):
        return "TorchSave"

    def matches(self, filename):
        # FIXME: It seems like this calls torch.jit.load when the file is zipped
        # and it thinks it's torchscript, so it will always match torchscript saved models too
        try:
            torch_load(filename)
            return True
        except Exception as e:
            # print(filename, e)
            return False


class TFSavedModel(ModelFormat):
    # Note: it seems like TensorFlow can also save checkpoints, but you need
    # to specify the model they came from in order to load them:
    # https://www.tensorflow.org/guide/checkpoint

    # Saved models themselves are directories containing multiple files, so
    # we are not expecting any suffixes
    expected_suffixes = [""]

    def __str__(self):
        return "TensorFlow SavedModel"

    def matches(self, filename):
        try:
            tf_saved_model_load(filename)
            return True
        except Exception as e:
            # print(filename, e)
            return False


class H5(ModelFormat):
    expected_suffixes = ["h5", "keras"]

    def __str__(self):
        return "H5"

    def matches(self, filename):
        try:
            keras_load(filename)
            return True
        except Exception as e:
            # print(filename, e)
            return False


class Onnx(ModelFormat):
    expected_suffixes = ["onnx", "pb"]

    def __str__(self):
        return "ONNX"

    def matches(self, filename):
        try:
            onnx_load(filename)
            return True
        except Exception as e:
            # print(filename, e)
            return False


class Jax(ModelFormat):
    expected_suffixes = ["jax"]

    def __str__(self):
        return "Jax"

    def matches(self, filename):
        # Calling restore() messes up logging, so we have to remove the installed
        # loggers each time
        # FIXME: maybe there's a better way to do this
        try:
            PyTreeCheckpointer().restore(filename)

            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            return True
        except Exception as e:
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            # print(filename, e)
            return False
        # return False


class MessagePack(ModelFormat):
    expected_suffixes = ["msgpack"]

    def __str__(self):
        return "MessagePack"

    def matches(self, filename):
        try:
            flax_msgpack_restore(open(filename, "rb").read())
            return True
        except Exception as e:
            return False


class SafeTensor(ModelFormat):
    expected_suffixes = ["safetensor", "safetensors"]

    def __str__(self):
        return "SafeTensor"

    def matches(self, filename):
        # Try all possible frameworks
        frameworks = ["pytorch", "tensorflow", "numpy", "jax", "mlx"]
        for framework in frameworks:
            try:
                safetensors_open(filename, framework=framework)
                return True
            except Exception as e:
                # print(e)
                pass

        return False


class AppleCoreMl(ModelFormat):
    # Note: Seems like this also loads protobuf files

    expected_suffixes = ["mlmodel", "mlpackage"]

    def __str__(self):
        return "Apple Core ML"

    def matches(self, filename):
        try:
            coreml_load(filename)
            return True
        except Exception as e:
            # print(e)
            return False


class Numpy(ModelFormat):
    expected_suffixes = ["npy", "npz"]

    def __str__(self):
        return "Numpy"

    def matches(self, filename):
        try:
            numpy_load(filename)
            return True
        except Exception as e:
            # print(e)
            return False


class Paddle(ModelFormat):
    # FIXME: this sometimes prints out a bunch of error messages when it tries
    # to load protobufs, but I can't find a good way to disable it
    # [libprotobuf ERROR
    # /Users/paddle/xly/workspace/6b5f2c56-ddc3-4da3-aa89-e4f3a21369ae/Paddle/third_party/protobuf/src/google/protobuf/message_lite.cc:133]
    # Can't parse message of type "paddle.framework.proto.ProgramDesc" because
    # it is missing required fields

    expected_suffixes = ["pdparams"]

    def __str__(self):
        return "Paddle"

    def matches(self, filename):
        try:
            # pdb.set_trace()
            paddle_load(filename)
            return True
        except Exception as e:
            # print(e)
            return False
        return False


class MLeap(ModelFormat):
    expected_suffixes = ["zip"]

    def __str__(self):
        return "MLeap"

    def matches(self, filename):
        # try:
        #     mleap_load(filename)
        #     return True
        # except Exception as e:
        #     # print(e)
        #     return False
        return False


def get_model_format(filename):
    suffix = ""
    if "." in filename:
        suffix = filename.split(".")[-1]

    matches = []

    for format_class in ModelFormat.__subclasses__():
        format = format_class()
        if format.matches(filename):
            logger.info(f"{filename} matches format {format}")
            matches.append(str(format))

            if suffix not in format.expected_suffixes:
                logger.warning(
                    f"{filename}'s suffix does not match expected suffixes for {format} ({', '.join(format.expected_suffixes)})"
                )

    if len(matches) > 1:
        logger.warning(f"{filename} matches more than one format: {', '.join(matches)}")
    # if len(matches) == 0:
    #     logger.error(f"{filename} does not match any model format!")
    return matches


def list_files(directory):
    for root, directories, files in os.walk(directory):
        for filename in files:
            yield os.path.abspath(os.path.join(root, filename))
        # We also return the directories because some formats (e.g., tensorflow
        # saved models) expect a whole directory of files
        for directory in directories:
            yield os.path.abspath(os.path.join(root, directory))
        for subdir in directories:
            subdir_path = os.path.join(root, subdir)
            yield from list_files(subdir_path)


def main():
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument("path", help="Path to stored models")

    args = arg_parser.parse_args()

    # Remove loggers installed by imported modules and install ours
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Maps files to their formats
    formats = {}

    for filename in list_files(args.path):
        matching_formats = get_model_format(filename)
        formats[filename] = matching_formats

    for file, mformats in formats.items():
        if len(mformats) > 0:
            print(file, mformats)


if __name__ == "__main__":
    main()
