"""
After downloading models and generating fickling traces (download_models.py),
use this script to analyze the output directory and produce a CSV of the
results.

Usage: analyze_traces.py <path to outdir with traces>
"""

import argparse
import dataclasses
import glob
import re
from pathlib import Path
from typing import List

NAME_EXT = "*.name"
TAGS_EXT = "*.tags"
TRACE_EXT = "*.trace"

@dataclasses.dataclass
class Repository:

    def __init__(self):
        self.name = ""
        self.tags = []
        self.imports = {}
        self.extensions = {}

    def get_csv(self, delimiter="|") -> str:
        outstr = self.name + delimiter + ','.join(self.tags) + delimiter
        for key in self.imports:
            outstr += key + delimiter
            outstr += ','.join(self.imports[key])
            outstr += delimiter
            outstr += ','.join(self.extensions[key])
            outstr += delimiter
        return outstr

def contains_import(line: str) -> bool:
    return line.startswith("from") or line.startswith("import")


def contains_extension(line: str) -> bool:
    return "UNPICKLER" in line


def extract_import(line: str) -> List[str]:

    return line

def extract_extension(line: str) -> List[str]:

    # This does not properly capture python function name rules, but is quick and dirty
    pattern = "UNPICKLER\.[a-zA-Z0-9_]*"
    return set(re.findall(pattern, line))

def analyze_trace(trace: str) -> (List[str], List[str]):

    # Given a file containing a pickle trace, extract relevant information
    # Relevant information:
    # - Imports (identified by "from" or "import"): just save entire line
    # - Calls to UNPICKLER custom functions: use a regular expression to
    #   extract method name, e.g. UNPICKLER.persistent_load(...)

    imports = set()
    extensions = set()
    with open(trace, "r") as fd:
        for line in fd:
            line = line.strip()
            if contains_import(line):
                imports.add(extract_import(line))
            elif contains_extension(line):
                extensions = extensions | extract_extension(line)
    return imports, extensions

def analyze_project(project_path: Path) -> None:

    project = Repository()

    name_glob_pattern = project_path / Path(NAME_EXT)
    name_files = glob.glob(str(name_glob_pattern))
    assert len(name_files) == 1
    with open(name_files[0], "r") as fd:
        project.name = fd.read().strip()
    #project.name = project_path.stem

    tags_glob_pattern = project_path / Path(TAGS_EXT)
    tags_files = glob.glob(str(tags_glob_pattern))
    assert len(tags_files) == 1
    with open(tags_files[0], "r") as fd:
        project.tags = fd.read().strip().split(',')
    #project.tags = ['PyTorch hub']

    traces_glob_pattern = project_path / Path('**') / Path(TRACE_EXT)
    traces_files = glob.glob(str(traces_glob_pattern), recursive=True)
    for trace_file in traces_files:
        model_name = Path(trace_file).stem
        imports, extensions = analyze_trace(trace_file)
        project.imports[model_name] = imports
        project.extensions[model_name] = extensions

    return project

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models")
    args = parser.parse_args()

    project_dirs = [x for x in Path(args.models).iterdir() if x.is_dir()]

    projects = []
    for project in project_dirs:
        projects.append(analyze_project(project))

    for project in projects:
        print(project.get_csv())

if __name__ == '__main__':
    main()
