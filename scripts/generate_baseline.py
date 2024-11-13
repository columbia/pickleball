import argparse
import json
from pathlib import Path

import download_model
import parsetrace
import modelunion


def generate_trace(model_path):

    trace = ''
    try:
        trace = download_model._generate_pytorch_trace(model_path, True)
    except ValueError:
        try:
            trace = download_model._generate_pytorch_trace(model_path, True)
        except RuntimeError as err:
            print("%s", err)

    return trace

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
        description=("Generate a baseline policy from a set of torch models"))
    parser.add_argument(
        'modelname',
        type=str,
        help='Name of the model (use Joern fullName format)')
    parser.add_argument(
        'modelsdir',
        metavar='F',
        type=Path,
        help='models to trace and generate policy for')
    parser.add_argument(
        'out',
        type=str,
        help='Name of output file'
    )

    args = parser.parse_args()

    policies = {}
    root_path = Path(args.modelsdir)
    for filename in root_path.rglob('pytorch_model.bin'):
    #for filename in args.filenames:
        # Create an opcode trace at {filename}.opcode
        print(f'tracing: {str(filename)}')
        file_trace = generate_trace(str(filename))
        # Create a JSON policyo

        try:
            with open(f'{str(filename)}.opcode', 'r', encoding='utf-8') as file:
                text_lines = file.readlines()
        except FileNotFoundError:
            print(f"Error: file {str(filename)}.opcode not found")
            continue

        
        policies[filename] = json.loads(parsetrace.parse_trace_to_json(text_lines))

    with open(args.out, 'w') as file:
        print(f'Writing output to: {args.out}')
        file.write(json.dumps(modelunion.model_union(policies.values(), args.modelname)))


