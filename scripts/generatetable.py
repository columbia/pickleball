#!/usr/bin/python3

import argparse
import pathlib
import tomllib
from typing import Dict, Any

import compare

LATEX_TABLE_HEADER = """
\\documentclass{article}
\\usepackage{booktabs} % For \\toprule and \\bottomrule
\\usepackage{graphicx} % Useful for better table formatting
\\usepackage[a4paper,margin=1in]{geometry} % Set margins for better layout

\\begin{document}

\\begin{table*}[t!]
\\centering
\\begin{tabular}{l | r r r | r r r r | r r r}
    \\toprule
    & \\multicolumn{3}{c|}{\\textbf{Imports}} & \\multicolumn{3}{c|}{\\textbf{Invocations}} & \\multicolumn{2}{c}{\\textbf{Loading}} \\\\
    \\textbf{Library} & Observed & Allowed & Stub Objects & Observed & Allowed & Stub Objects & \\# Models & \\# Executed (\\%) \\\\
    \\toprule
"""

LATEX_TABLE_FOOTER = """
    \\bottomrule
\\end{tabular}
\\end{table*}

\\end{document}
"""

def generate_table(results: Dict[str, Any]) -> str:

    latex_table = LATEX_TABLE_HEADER

    for library, values in results.items():
        global_values = values["global_lines"]
        reduce_values = values["reduce_lines"]

        globals_observed = global_values["in_baseline_not_inferred"] + global_values["in_both"]
        reduces_observed = reduce_values["in_baseline_not_inferred"] + reduce_values["in_both"]

        globals_allowed = global_values["in_inferred_not_baseline"] + global_values["in_both"]
        reduces_allowed = reduce_values["in_inferred_not_baseline"] + reduce_values["in_both"]

        globals_stubbed = global_values["in_baseline_not_inferred"]
        reduces_stubbed = reduce_values["in_baseline_not_inferred"]

        row = f"{library} & {globals_observed} & {globals_allowed} & {globals_stubbed} & {reduces_observed} & {reduces_allowed} & {reduces_stubbed} & TBD & TBD (X\\%) \\\\\n"
        latex_table += row

    latex_table += "\\midrule\n"

    latex_table += "\\textbf{Total} & & & & & & & TBD & TBD (X\\%) \\\\\n"
    latex_table += "\\bottomrule\n"

    latex_table += LATEX_TABLE_FOOTER
    return latex_table

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=("Generate LaTeX table summarizing results of policy "
                     "generation."))

    parser.add_argument(
        "manifest",
        type=pathlib.Path,
        help="Path to manifest file")

    args = parser.parse_args()

    # Read manifest
    with open(args.manifest, "rb") as manifest_file:
        config = tomllib.load(manifest_file)

    policies_dir = pathlib.Path(config["system"]["policies_dir"])

    # For each library in the manifest, compare the baseline policy to the
    # generated policy. Collect values.
    library_results = {}
    for library in config["libraries"].keys():

        policy_path = policies_dir / pathlib.Path(f"{library}.json")
        baseline_path = policies_dir / pathlib.Path(f"baseline/{library}.json")

        result = compare.compare_json_files(str(baseline_path), str(policy_path))
        library_results[library] = result

    #print(library_results)
    # Generate Table with collected values, outputting LaTeX code.

    print(generate_table(library_results))