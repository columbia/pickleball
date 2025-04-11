#!/usr/bin/python3

import argparse
import pathlib
import tomllib
from typing import Dict, Any
from dataclasses import dataclass

import compare

LATEX_TABLE_HEADER = """
\\documentclass{article}
\\usepackage{booktabs} % For \\toprule and \\bottomrule
\\usepackage{graphicx} % Useful for better table formatting
\\usepackage[a4paper,margin=1in]{geometry} % Set margins for better layout

\\begin{document}

\\begin{table*}[t!]
\\centering
\\resizebox{\\textwidth}{!}{%
\\begin{tabular}{l | r r r | r r r r | r r r}
    \\toprule
    & \\multicolumn{3}{c|}{\\textbf{Imports}} & \\multicolumn{3}{c|}{\\textbf{Invocations}} & \\multicolumn{2}{c}{\\textbf{Loading}} \\\\
    \\textbf{Library} & Observed & Allowed & Stub Objects & Observed & Allowed & Stub Objects & \\# Models & \\# Executed (\\%) \\\\
    \\toprule
"""

LATEX_TABLE_FOOTER = """
    \\bottomrule
\\end{tabular}
} % \\resizebox
\\end{table*}

\\end{document}
"""


@dataclass(slots=True)
class Library(object):
    name: str
    globals_observed: int = 0
    globals_inferred: int = 0
    globals_missed: int = 0
    reduces_observed: int = 0
    reduces_inferred: int = 0
    reduces_missed: int = 0
    models_attempted: int = 0
    models_loaded: int = 0


def generate_table(results: Dict[str, Library]) -> str:

    latex_table = LATEX_TABLE_HEADER

    for library, values in results.items():

        rate = values.models_loaded / values.models_attempted if values.models_attempted != 0 else 0

        row = (f"{library} & {values.globals_observed} & {values.globals_inferred} & "
               f"{values.globals_missed} & {values.reduces_observed} & {values.reduces_inferred} & "
               f"{values.reduces_missed} & {values.models_attempted} & {values.models_loaded} "
               f"({rate * 100:.1f}\\%) \\\\\n")
        latex_table += row

    total_attempted = sum([library.models_attempted for library in results.values()])
    total_loaded = sum([library.models_loaded for library in results.values()])
    total_rate = total_loaded / total_attempted if total_attempted != 0 else 0

    latex_table += "\\midrule\n"

    latex_table += f"\\textbf{{Total}} & & & & & & & {total_attempted} & {total_loaded} ({total_rate * 100:.1f}\\%) \\\\\n"
    latex_table += "\\bottomrule\n"

    latex_table += LATEX_TABLE_FOOTER
    return latex_table

def print_macros(library: Library):

    # Example: \newcommand{conchImportsObserved}{24}
    # Add double {{}} to escape them in the format string
    template = "\\newcommand{{\\{libraryname}{mode}{valuetype}}}{{{value}}}"

    print(template.format(name=library.name, mode="Imports", valueType="Observed",
                    value=library.globals_observed))
    print(template.format(name=library.name, mode="Imports", valueType="Allowed",
                    value=library.globals_allowed))

def read_last_line(filepath: pathlib.Path) -> str:

    with filepath.open("rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_line = f.readline().decode().strip()
    return last_line


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=("Generate LaTeX table summarizing results of policy "
                     "generation."))

    parser.add_argument(
        "manifest",
        type=pathlib.Path,
        help="Path to manifest file")
    parser.add_argument(
        "--enforcement-results",
        type=pathlib.Path,
        default=None,
        help="Path to directory containing results from enforcement experiments"
    )
    parser.add_argument(
        "--output-macros",
        action="store_true",
        help=("Output LaTeX Macro definitions for variable names, rather than"
        "for a table"))

    args = parser.parse_args()

    # Read manifest
    with open(args.manifest, "rb") as manifest_file:
        config = tomllib.load(manifest_file)

    policies_dir = args.manifest.parent / pathlib.Path(config["system"]["policies_dir"])

    # For each library in the manifest, compare the baseline policy to the
    # generated policy. Collect values.
    libraries = {}
    for library_name in config["libraries"].keys():

        policy_path = policies_dir / pathlib.Path(f"{library_name}.json")
        baseline_path = policies_dir / pathlib.Path(f"baseline/{library_name}.json")

        result = compare.compare_json_files(str(baseline_path), str(policy_path))
        library = Library(name=library_name)

        global_values = result["global_lines"]
        reduce_values = result["reduce_lines"]

        library.globals_observed = (global_values["in_baseline_not_inferred"] +
                                    global_values["in_both"])
        library.reduces_observed = (reduce_values["in_baseline_not_inferred"] +
                                    reduce_values["in_both"])

        library.globals_inferred = (global_values["in_inferred_not_baseline"] +
                                   global_values["in_both"])
        library.reduces_inferred = (reduce_values["in_inferred_not_baseline"] +
                                   reduce_values["in_both"])

        library.globals_missed = global_values["in_baseline_not_inferred"]
        library.reduces_missed = reduce_values["in_baseline_not_inferred"]

        libraries[library_name] = library

    if args.enforcement_results:
        # Read the values from the enforcement results and add them to the
        # results dictionary
        result_files = [f for f in args.enforcement_results.iterdir() if f.is_file()]

        for result_file in result_files:
            if result_file.suffix != ".log":
                continue
            library_name = result_file.stem

            last_line = read_last_line(result_file)
            # Assumes that the last line of the file contains "success:total"
            assert len(last_line.split(":")) == 2, f"{result_file}"
            success_str, total_str = last_line.split(":")
            success = int(success_str)
            total = int(total_str)

            assert library_name in libraries.keys()

            libraries[library_name].models_attempted = total
            libraries[library_name].models_loaded = success

    # Generate Table with collected values, outputting LaTeX code.
    if args.output_macros:
        for library in libraries:
            print_macros(library)
            print()
    else:
        print(generate_table(libraries))
