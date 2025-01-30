#!/usr/bin/python3

import importlib
import pathlib
import os
import sys
import tomllib

# Get the parent directory of the current script
# Add parent directory to sys.path if not already added
# Import the module from the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
module_name = "pickleball-generate"
pickleball = importlib.__import__(module_name)

MANIFEST = 'manifest.toml'

with open(MANIFEST, 'rb') as manifest_file:
    config = tomllib.load(manifest_file)

MEM = config['system']['mem']
LIBRARIES_DIR = pathlib.Path(config['system']['libraries_dir'])
CACHE_DIR = pathlib.Path(config['system']['cache_dir'])
POLICIES_DIR = pathlib.Path(config['system']['policies_dir'])
JOERN_DIR = pathlib.Path(config['system']['joern_dir'])
ANALYZER_PATH = pathlib.Path(config['system']['analyzer_path'])

if MEM == 'all':
    mem = pickleball.get_available_mem()

for library, values in config['libraries'].items():

    library_path = LIBRARIES_DIR / pathlib.Path(values['library_path'])
    model_class = values['model_class']
    use_cpg = values['use_cpg']
    ignore_paths = values['ignore_paths'] if 'ignore_paths' in values else ''
    policy_path = POLICIES_DIR / pathlib.Path(f'{library}.json')
    cpg_path = pathlib.Path("/tmp") / pathlib.Path(f'{library}.cpg')

    # TODO: Logging
    # TODO: Timing
    print(f'Generating CPG and policy for: {library}')
    pickleball.create_cpg(
        library_path,
        JOERN_DIR,
        mem,
        out_path=cpg_path,
        ignore_paths=ignore_paths,
        use_cpg=use_cpg
    )
    pickleball.generate_policy(
        cpg_path,
        model_class,
        mem,
        ANALYZER_PATH,
        JOERN_DIR,
        CACHE_DIR,
        policy_path
    )