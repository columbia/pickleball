import argparse
import contextlib
import logging
import sys

if sys.version_info >= (3, 9):
    from ast import unparse
else:
    from astunparse import unparse

from fickling import fickle, tracing
from fickling.pytorch import PyTorchModelWrapper

# The fickling module generates a lot of printed output statements when tracing
# a pickle program. I use this dummy file and context manager to silence the
# output statements to avoid cluttering stdout.
class DummyFile(object):
    def write(self, x):
        pass

    def flush(self):
        pass


# Used to prevent cluttering stdout when generating fickling trace. See comment
# above DummyFile.
@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = save_stdout

def _generate_stacked_trace(model_path: str) -> str:

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
            pickled, first_variable_id=var_id, result_variable=f"result{i}"
        )
        model_trace = tracing.Trace(interpreter)
        with nostdout():
            collected_trace = model_trace.run()
        trace += unparse(collected_trace)
        var_id = interpreter.next_variable_id

    return trace


def _generate_pytorch_trace(model_path: str) -> str:

    pytorch_model = PyTorchModelWrapper(model_path)
    try:
        _ = pytorch_model.formats
    except ValueError as err:
        logging.error("Unable to identify model format: %s", err)
        raise ValueError(err) from err

    interpreter = fickle.Interpreter(pytorch_model.pickled, first_variable_id=0)
    model_trace = tracing.Trace(interpreter)
    with nostdout():
        collected_trace = model_trace.run()

    return unparse(collected_trace)

def trace_model(model_path: str) -> str:
    logging.info("Generating trace for model: %s", model_path)
    trace = ""
    # TODO: Tidy this up. Currently, the code tries to first use the fickling
    # PyTorchWrapper API to interact with the model, but this may fail when the
    # model is a 'stacked' pickle file, in which case I use the StackedPickle
    # API. I should be able to test ahead of time for the model type and then
    # select the right approach.
    try:
        trace = _generate_pytorch_trace(model_path)
    except ValueError:
        logging.warning("- Could not trace as PyTorch model. Trying stacked pickle")
        try:
            trace = _generate_stacked_trace(model_path)
        except RuntimeError as err:
            logging.warning("- Unable to generate trace for model: %s", model_path)
            logging.warning("%s", err)

    return trace

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--modelpath",
        help="Path to PyTorch model")
    parser.add_argument(
        "--out",
        help="Path to output file. If not specified, trace will be printed to stdout")
    args = parser.parse_args()

    model_trace: str = trace_model(args.modelpath)

    if args.out:
        with open(args.out, 'wb') as f:
            f.write(model_trace)
    else:
        print(model_trace)
