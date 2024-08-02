import argparse
import sys

if sys.version_info >= (3, 9):
    from ast import unparse
else:
    from astunparse import unparse

from fickling import tracing
from fickling import fickle
from fickling.pytorch import PyTorchModelWrapper


def trace(model):

    interpreter = fickle.Interpreter(
        model.pickled,
        first_variable_id=0,
        result_variable="result0")
    trace = tracing.Trace(interpreter)
    return unparse(trace.run())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="path to PyTorch model to identify")
    parser.add_argument("--trace", action="store_true", default=False,
        help="if set, trace of model will be saved")
    args = parser.parse_args()

    pytorch_model = PyTorchModelWrapper(args.model)
    try:
        formats = pytorch_model.formats
    except ValueError as err:
        formats = err
        print(args.model)
        print(formats)
        sys.exit(-1)

    if args.trace:
        model_trace = trace(pytorch_model)
        with open(f'{args.model}.trace', 'w') as f:
            f.write(model_trace)


    print(args.model)
    print(formats)
