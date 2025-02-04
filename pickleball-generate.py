#!/usr/bin/python3

import argparse
import pathlib
import subprocess

ANALYZE_PATH = pathlib.Path('analyze/analyze.sc')

def get_available_mem() -> int:
    """
    Determine available system RAM in KiB.
    """

    mem_total = ''

    with open("/proc/meminfo", "r") as f:
        for line in f:
            if line.startswith("MemTotal"):
                # Split the line and extract the second column
                mem_total = line.split()[1]
                break

    # Assumes that the read value is convertible to an integer.
    # TODO: Check assumption or handle error.
    return int(mem_total)

def create_cpg(
        library_path: pathlib.Path,
        joern_path: pathlib.Path,
        system_mem: int,
        out_path: pathlib.Path = pathlib.Path('/tmp/out.cpg'),
        ignore_paths: str = '',
        use_cpg: bool = False,
        dry_run: bool = False):
    """Generate a CPG (or AST) of the ML library code."""

    if use_cpg:
        joern_utility = joern_path / pathlib.Path('joern-parse')
    else:
        joern_utility = joern_path / pathlib.Path('joern-cli/target/universal/stage/pysrc2cpg')

    cmd = [
        str(joern_utility),
        f'-J-Xmx{system_mem}k',
        str(library_path),
        '-o', str(out_path),
    ]
    if ignore_paths:
        cmd.append(f'--ignore-paths={ignore_paths}')

    print(f'Creating CPG:\n'
          f'{" ".join(cmd)}')

    if not dry_run:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)


def generate_policy(
        cpg_path: pathlib.Path,
        model_class: str,
        system_mem: int,
        analyzer_path: pathlib.Path,
        joern_path: pathlib.Path,
        cache_path: pathlib.Path,
        policy_path: pathlib.Path,
        #log_path: pathlib.Path,
        dry_run: bool = False):
    """Generate a model loading policy for the ML library."""

    cmd = [
        str(joern_path / pathlib.Path("joern")),
        f'--script', str(analyzer_path),
        f'-J-Xmx{system_mem}k',
        f'--param', f'inputPath={str(cpg_path)}',
        f'--param', f'modelClass={model_class}',
        f'--param', f'outputPath={str(policy_path)}'
    ]

    if cache_path:
        cmd.append('--param')
        cmd.append(f'cache={str(cache_path)}')

    print(f'Analyzing CPG:\n'
          f'{" ".join(cmd)}')

    if not dry_run:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
            description=("Generate a model loading policy for a ML library "
                         "model class"))
    # Required arguments
    parser.add_argument(
            '--library-path',
            type=pathlib.Path,
            required=True,
            help='Path to the ML library source code directory')

    parser.add_argument(
            '--model-class',
            type=str,
            required=True,
            help='Model class name')

    parser.add_argument(
            '--joern-path',
            type=pathlib.Path,
            default=pathlib.Path('/joern'),
            help='Path to the joern directory')

    parser.add_argument(
            '--policy-path',
            type=pathlib.Path,
            default=pathlib.Path('policy.json'),
            help='Output policy path')

    parser.add_argument(
            '--ignore-paths',
            type=str,
            default='',
            help=('Paths in the ML library to ignore during analysis (e.g., '
                  'tests directories)'))

    parser.add_argument(
            '--cache-path',
            type=pathlib.Path,
            default=pathlib.Path(''),
            help="Path to cache directory")

    parser.add_argument(
            '--use-cpg',
            action='store_true',
            help=('Enable CPG mode (enhanced over AST). Note: this may '
                  'introduce instability in Joern analysis.'))

    parser.add_argument(
            '--dry-run',
            action='store_true',
            help=('Dry run without executing the Joern utility.'))

    args = parser.parse_args()

    available_mem = get_available_mem()
    # TODO: Configure
    intermediate_cpg = pathlib.Path('/tmp/out.cpg')

    create_cpg(
        args.library_path,
        args.joern_path,
        available_mem,
        out_path=intermediate_cpg,
        ignore_paths=args.ignore_paths,
        dry_run=args.dry_run)

    generate_policy(
        intermediate_cpg,
        args.model_class,
        available_mem,
        ANALYZE_PATH,
        args.joern_path,
        args.cache_path,
        args.policy_path,
        dry_run=args.dry_run)
