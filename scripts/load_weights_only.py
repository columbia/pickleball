import argparse
from pathlib import Path

import torch

def load(model_path):
    torch.load(model_path, weights_only=True)


def main():

    parser = argparse.ArgumentParser("Load a model using the weights-only-unpickler")

    parser.add_argument(
        'modelsdir',
        metavar='F',
        type=Path,
        help='models to trace and generate policy for'
    )
    parser.add_argument(
        '--out',
        type=str,
        help='Name of output file'
    )
    parser.add_argument(
        '--modelname',
        type=str,
        default='pytorch_model.bin',
        help='Name of the model (defaults to \'pytorch_model.bin\')')

    args = parser.parse_args()

    attempts = 0
    success = 0
    fails = 0
    models = {}

    root_path = Path(args.modelsdir)
    for filename in root_path.rglob(args.modelname):
        print(f'loading: {str(filename)}')

        attempts += 1
        try:
            load(str(filename))
            success += 1
            models[str(filename)] = 'SUCCESS'
        except torch._pickle.UnpicklingError:
            fails += 1
            models[str(filename)] = 'FAILURE'

    with open(args.out, 'w') as file:
        file.write(f'Attempted models: {attempts}')
        file.write(f'Successful loads: {success}')
        file.write(f'Failed loads: {fails}')
        for key, value in models.items():
            file.write(f'{key}: {value}\n')


if __name__ == '__main__':
    main()
