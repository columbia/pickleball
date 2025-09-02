#!/usr/bin/python3

import argparse
import subprocess
import sys
from typing import Optional
from pathlib import Path

ANALYZE_PATH = Path('analyze/analyze.sc')

class JoernRuntimeError(Exception):
    """Error raised when Joern crashes"""


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


def gb_to_kb(mem_gb: int) -> int:
    """
    Convert value in GiB to KiB.
    """
    return mem_gb << 20

def create_cpg(
        library_path: Path,
        joern_path: Path,
        system_mem: int,
        out_path: Path = Path('/tmp/out.cpg'),
        ignore_paths: str = '',
        use_cpg: bool = False,
        dry_run: bool = False):
    """Generate a CPG (or AST) of the ML library code."""

    if use_cpg:
        joern_utility = joern_path / Path('joern-parse')
        language_switch = "--language"
        language_option = "PYTHONSRC"
        frontend_switch = "--frontend-args"
    else:
        joern_utility = joern_path / Path('joern-cli/target/universal/stage/pysrc2cpg')
        language_switch = ""
        language_option = ""
        frontend_switch = ""


    cmd = [
        str(joern_utility),
        language_switch, language_option,
        f'-J-Xmx{system_mem}k',
        str(library_path),
        '-o', str(out_path),
        frontend_switch
    ]
    if ignore_paths:
        cmd.append(f'--ignore-paths={ignore_paths}')

    # Remove any empty arguments from the command string
    cmd = list(filter(lambda x : x, cmd))

    print(f'Creating CPG:\n'
          f'{" ".join(cmd)}')

    if dry_run:
        return

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print(result.stdout)


def generate_policy(
        cpg_path: Path,
        model_class: str,
        system_mem: int,
        analyzer_path: Path,
        joern_path: Path,
        cache_path: Path,
        policy_path: Path,
        log_path: Optional[Path] = None,
        verbose: bool = False,
        dry_run: bool = False):
    """Generate a model loading policy for the ML library."""

    cmd = [
        str(joern_path / Path("joern")),
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

    if dry_run:
        return

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise JoernRuntimeError(f"Joern exit ({result.returncode}): {result.stderr}")

    if log_path:
        log_path.write_text(result.stdout)

    if verbose:
        print(result.stdout)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
            description=("Generate a model loading policy for a ML library "
                         "model class"))
    # Required arguments
    parser.add_argument(
            '--library-path',
            type=Path,
            required=True,
            help='Path to the ML library source code directory')

    parser.add_argument(
            '--model-class',
            type=str,
            required=True,
            help='Model class name (use Joern fully-qualified name format)')

    parser.add_argument(
            '--joern-path',
            type=Path,
            default=Path('/joern'),
            help='Path to the joern directory')

    parser.add_argument(
            '--policy-path',
            type=Path,
            default=Path('policy.json'),
            help='Output policy path')

    parser.add_argument(
            '--ignore-paths',
            type=str,
            default='',
            help=('Paths in the ML library to ignore during analysis (e.g., '
                  'tests directories)'))

    parser.add_argument(
            '--cache-path',
            type=Path,
            default=Path(''),
            help="Path to cache directory")

    parser.add_argument(
            '--use-cpg',
            action='store_true',
            help=('Enable CPG mode (enhanced over AST). Note: this may '
                  'introduce instability in Joern analysis'))

    parser.add_argument(
            '--dry-run',
            action='store_true',
            help=('Dry run without executing the Joern utility'))

    parser.add_argument(
            '--mem',
            type=int,
            help=('Maximum amount of system RAM (in GB) to use. If not provided, '
                  'defaults to using all available memory.'))
    parser.add_argument(
            '--only-cpg',
            action='store_true',
            help=('Only create CPG and return (without also generating policy)'))
    args = parser.parse_args()

    if args.mem:
        available_mem = gb_to_kb(args.mem)
    else:
        available_mem = get_available_mem()

    # TODO: Configure
    intermediate_cpg = Path('/tmp/out.cpg')

    create_cpg(
        args.library_path,
        args.joern_path,
        available_mem,
        out_path=intermediate_cpg,
        ignore_paths=args.ignore_paths,
        dry_run=args.dry_run)

    if args.only_cpg:
        sys.exit(0)

    generate_policy(
        intermediate_cpg,
        args.model_class,
        available_mem,
        ANALYZE_PATH,
        args.joern_path,
        args.cache_path,
        args.policy_path,
        dry_run=args.dry_run)
