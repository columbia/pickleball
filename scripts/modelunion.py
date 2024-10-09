"""
Given a list of model traces structured as JSON files, output the union of all
of the traces as a JSON file.
"""

import json
import argparse

def model_union(models, model_name):
    all_globals = set()
    all_reduces = set()

    for obj in models:
        all_globals.update(obj.get("globals", []))
        all_reduces.update(obj.get("reduces", []))

    result = {
        model_name: {
            "globals": list(all_globals),
            "reduces": list(all_reduces)
        }
    }

    return result

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Process a list of JSON files and compute union of "
            "GLOBALS and REDUCES fields."))

    parser.add_argument(
        'modelname',
        type=str,
        help='Name of the model (use Joern fullName format)')

    # Add argument to accept a list of file names
    parser.add_argument(
        'filenames',
        metavar='F',
        type=str,
        nargs='+',
        help='JSON files to be processed')

    # Parse the arguments
    args = parser.parse_args()

    json_objects = []

    # Read each file and load it as a JSON object
    for filename in args.filenames:
        with open(filename, 'r', encoding='utf-8') as fd:
            json_data = json.load(fd)
            json_objects.append(json_data)

    result = model_union(json_objects, args.modelname)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
