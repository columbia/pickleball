#!/usr/bin/python3

import argparse
import importlib
import pathlib
import os
import sys
import tomllib

from dataclasses import dataclass
from typing import Tuple, List, Dict

# This is hacky - because the module name is 'pickleball-generate' (with a dash)
# and in a parent directory.
# - Get the parent directory of the current script
# - Add parent directory to sys.path if not already added
# - Import the module from the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
module_name = "pickleball-generate"
pickleball = importlib.__import__(module_name)

OUTPATH = pathlib.Path('/tmp')


@dataclass
class SystemConfig(object):
    mem: int
    libraries_dir: pathlib.Path
    cache_dir: pathlib.Path
    policies_dir: pathlib.Path
    joern_dir: pathlib.Path
    analyzer_path: pathlib.Path

@dataclass
class LibraryConfig(object):
    name: str
    library_path: pathlib.Path
    model_class: str
    cpg_mode: str
    ignore_paths: str
    policy_path: pathlib.Path
    cpg_path: pathlib.Path
    log_path: pathlib.Path


# Parse the manifest file into a SystemConfig and and list of LibraryConfigs
def parse_manifest(manifest: pathlib.Path) -> Tuple[SystemConfig, List[LibraryConfig]]:

    with open(manifest, 'rb') as manifest_file:
        config = tomllib.load(manifest_file)

    mem: int = config['system']['mem']
    libraries_dir = pathlib.Path(config['system']['libraries_dir'])
    cache_dir = pathlib.Path(config['system']['cache_dir'])
    policies_dir = pathlib.Path(config['system']['policies_dir'])
    joern_dir = pathlib.Path(config['system']['joern_dir'])
    analyzer_path = pathlib.Path(config['system']['analyzer_path'])

    systemcfg = SystemConfig(mem=mem, libraries_dir=libraries_dir,
                        cache_dir=cache_dir, policies_dir=policies_dir,
                        joern_dir=joern_dir, analyzer_path=analyzer_path)

    def parse_library_config(library_name: str, library_setting: Dict[str, str],
                            systemcfg: SystemConfig):

        library_path = systemcfg.libraries_dir / pathlib.Path(library_setting['library_path'])
        model_class = library_setting['model_class']
        cpg_mode = library_setting['use_cpg']
        ignore_paths = library_setting['ignore_paths'] if 'ignore_paths' in library_setting else ''
        policy_path = systemcfg.policies_dir / pathlib.Path(f'{library_name}.json')
        cpg_path = OUTPATH / pathlib.Path(f'{library_name}.cpg')
        log_path = OUTPATH / pathlib.Path(f'{library_name}.log')

        return LibraryConfig(name=library_name, library_path=library_path,
                             model_class=model_class, cpg_mode=cpg_mode,
                             ignore_paths=ignore_paths, policy_path=policy_path,
                             cpg_path=cpg_path, log_path=log_path)

    # Run parse_library_config on each library entry in the manifest file.
    librarycfgs = [parse_library_config(library, values, systemcfg) for library, values in config['libraries'].items()]

    return systemcfg, librarycfgs

def generate_policy(librarycfg: LibraryConfig, systemcfg: SystemConfig, mem: int) -> None:

    # TODO: Timing
    print('-------------------------------------------------------------')
    print(f'Generating CPG and policy for: {librarycfg.name}')
    pickleball.create_cpg(
        librarycfg.library_path,
        systemcfg.joern_dir,
        systemmem,
        out_path=librarycfg.cpg_path,
        ignore_paths=librarycfg.ignore_paths,
        use_cpg=librarycfg.cpg_mode
    )
    pickleball.generate_policy(
        librarycfg.cpg_path,
        librarycfg.model_class,
        systemmem,
        systemcfg.analyzer_path,
        systemcfg.joern_dir,
        systemcfg.cache_dir,
        librarycfg.policy_path,
        log_path=librarycfg.log_path
    )


def print_libraries(librarycfs: List[LibraryConfig]) -> None:

    for library in librarycfgs:
        print(library.name)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Generate all policies defined for an experiment")
    parser.add_argument(
        "manifest",
        type=pathlib.Path,
        help="Path to manifest file describing experiment setup"
    )
    parser.add_argument(
        "--list-libraries",
        action='store_true',
        help="List all libraries in manifest"
    )
    parser.add_argument(
        "--fixtures",
        nargs="*",
        help=("A list of individual libraries to evaluate. If none are provided, "
            "defaults to generating policies for all libraries"),
        default=[]
    )
    args = parser.parse_args()

    systemcfg, librarycfgs = parse_manifest(args.manifest)

    if args.list_libraries:
        print_libraries(librarycfgs)
        sys.exit(0)

    if args.fixtures:
        # Filter the libraries specified in the fixture list
        evaluation_libraries = [library.name in args.fixtures for library in librarycfgs]
    else:
        # Otherwise, use all libraries in the manifest
        evaluation_libraries = librarycfgs

    if systemcfg.mem == 0:
        systemmem = pickleball.get_available_mem()
    else:
        systemmem = pickleball.gb_to_kb(systemcfg.mem)

    for librarycfg in evaluation_libraries:
        generate_policy(librarycfg, systemcfg, systemmem)
