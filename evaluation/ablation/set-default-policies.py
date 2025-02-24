import argparse
import json
import tomllib

from pathlib import Path

if __name__ == '__main__':

    # For each library in the toml manifest, write a "default" policy to the
    # output directory.

    # Inputs:
    # - manifest file
    # - default policy path
    # - output directory

    parser = argparse.ArgumentParser(
            description=("Prepare ablation study by setting all policies to "
                         "default."))
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to manifest file describing evaluation setup")
    parser.add_argument(
        "--default-policy",
        type=Path,
        help="Path to default policy file")
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to output directory where each policy will be written")
    args = parser.parse_args()

    with open(args.manifest, 'rb') as manifest_file:
        config = tomllib.load(manifest_file)

    libraries = [(library, values["model_class"]) for library, values in config['libraries'].items()]

    # Ensure that output is a directory
    assert args.output.is_dir()

    # Read default config into JSON object
    default_policy = json.loads(args.default_policy.read_text())

    for library, model_class in libraries:
        policy = {model_class: default_policy["torch/nn.py:<module>.Module"]}
        outfile = args.output / Path(f"{library}.json")
        outfile.write_text(json.dumps(policy, indent=2), encoding="utf-8")
