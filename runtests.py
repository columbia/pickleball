# For each sub-directory in the pickle-defense/analyze/tests/ directory:
# - Assume subdir has src/ directory containing test target.
# - Assume subdir has models/ directory containing class subdirectories
#   - Each class subdir contains: one or more .pkl file
#   - Each class subdir contains a 'metadata' file containing the Joern
#     fullname for the class type decl.
# - Generate fickling trace and json policy description for each model
#   - input: subdir/class/*.pkl
#   - output: subdir/class/*.trace
#   - output: subdir/class/*.json
# - Generate the fixture baseline policy for each class
#   (union of all policies generated per model)
#   - input: subdir/class/*.json
#   - input: subdir/class/metadata
#   - output: subdir/class/baseline.json
# - Generate Joern CPG
#   - input: subdir/src/
#   - output: subdir/out.cpg
# - Generate inferred policy for each class
#   - input: subdir/out.cpg
#   - input: subdir/*/metadata
#   - output: subdir/*/inferred.json
# - Report F1 score for each inferred policy compared to baseline:
#   - input: subdir/*/inferred.json
#   - input: subdir/*/baseline.json
#   - output: subdir/*/result.json

import pathlib
import subprocess
from typing import Tuple

from scripts import compare

# Hardcoded for docker container paths
# TODO: Make configurable
PATH_TO_JOERN = pathlib.Path('/joern')
PATH_TO_ANALYSIS_SCRIPT = pathlib.Path('/pickle-defense/analyze/analyze.sc')
PATH_TO_FIXTURES = pathlib.Path('/pickle-defense/analyze/tests/')

RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
RESET = '\033[0m'

FIXTURES = [
    'no-inheritance',
    'simple-inheritance',
    'multiple-inheritance',
    'dictionary-types',
    'interprocedural-attribute-writes',
    'reduce'
]

# Create CPG for
def create_cpg(fixture_path: pathlib.Path, output_path: pathlib.Path) -> bool:
    """Create Joern CPG for test fixture by invoking joern-parse

    Writes CPG in test fixture directory.
    """

    print(f'- Creating CPG: {fixture_path}')
    joern_parse_path = PATH_TO_JOERN / pathlib.Path('joern-parse')
    target_code = fixture_path / pathlib.Path('src')
    command = [str(joern_parse_path), str(target_code), '-o', str(output_path)]
    print(f'- Command: {" ".join(command)}')
    result = subprocess.run(command, capture_output=True, check=False)

    return result.returncode == 0


# Create inferred policy by running analysis script
def infer_policy(cpg_path: pathlib.Path, model_class: str, output_path: pathlib.Path) -> str:
    """Run inference analysis for a given CPG and model class by invoking joern.

    Writes the analysis output as JSON to the output_path.
    """

    print('- Inferring policy')
    joern_path = PATH_TO_JOERN / pathlib.Path('joern')
    command = [
        str(joern_path),
        '--script',
        str(PATH_TO_ANALYSIS_SCRIPT),
        '--param',
        f'inputPath={str(cpg_path)}',
        '--param',
        f'modelClass={model_class}',
        '--param',
        f'outputPath={str(output_path)}'
    ]
    print(f'- Command: {" ".join(command)}')
    result = subprocess.run(command, capture_output=True, check=False)

    if result.returncode != 0:
        print(result.stderr)

    return result.returncode == 0

def compare_policies(policy: pathlib.Path, baseline: pathlib.Path) -> Tuple[float, float]:

    result = compare.compare_json_files(str(policy), str(baseline))
    global_f1 = result["global_lines"]["f1"]
    reduce_f1 = result["reduce_lines"]["f1"]
    return (global_f1, reduce_f1)

def main():

    for fixture in FIXTURES:
        print(f'{BLUE}[*] Test fixture: {fixture}{RESET}')
        fixture_path = PATH_TO_FIXTURES / pathlib.Path(fixture)
        cpg_path = fixture_path / pathlib.Path('out.cpg')

        if not create_cpg(fixture_path, cpg_path):
            print(f'error creating CPG for fixture {fixture}')
            return -1

        # For each model class, infer a policy and compare it to the policy
        # baseline.
        models_path = fixture_path / pathlib.Path('models')
        model_dirs = [subdir for subdir in models_path.iterdir() if subdir.is_dir()]
        for model_dir in model_dirs:
            model_class_file = model_dir / pathlib.Path('metadata')
            with open(str(model_class_file), 'r', encoding='utf-8') as metadata_fd:
                model_class_name = metadata_fd.read().strip()
            inferred_path = model_dir / pathlib.Path('inferred.json')
            if not infer_policy(cpg_path, model_class_name, inferred_path):
                print(f'error inferring policy for model {model_dir.name}')
                return -1

            baseline_path = model_dir / pathlib.Path('baseline.json')
            globals_f1, reduces_f1 = compare_policies(inferred_path, baseline_path)

            if globals_f1 < 1.0 or reduces_f1 < 1.0:
                print(f"{RED}[-] FAIL: globals F1 {globals_f1}; reduces F1 {reduces_f1}{RESET}")
            else:
                print(f"{GREEN}[+] PASS{RESET}")


if __name__ == '__main__':
    main()