import pickle, torch, argparse
from pathlib import Path
'''
Did this similar to load_weights_only.py
'''

def pickleload(model_path):
    pickle.load(open(model_path, "rb"))

def torchload(model_path):
    torch.load(model_path, map_location=torch.device('cpu'))

def main():

    parser = argparse.ArgumentParser("Load a model using pickle or torch")

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
        help='Name of the model (defaults to \'pytorch_model.bin\')'
    )
    parser.add_argument(
        '--loader',
        type=str,
        default='torch',
        help='Load using torch or pickle'
    )

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
            if args.loader == "torch":
                torchload(str(filename))
            else:
                pickleload(str(filename))
            success += 1
            models[str(filename)] = 'SUCCESS'
        except pickle.UnpicklingError as err:
            fails += 1
            models[str(filename)] = f'FAILURE: {err}'

    with open(args.out, 'w') as file:
        file.write(f'Attempted models: {attempts}\n')
        file.write(f'Successful loads: {success}\n')
        file.write(f'Failed loads: {fails}\n')
        for key, value in models.items():
            file.write(f'{key}: {value}\n')


if __name__ == '__main__':
    main()
