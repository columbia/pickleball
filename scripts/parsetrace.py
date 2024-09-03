"""
Given a fickling trace of a model, identify all GLOBAL imports and REDUCE
callables.
"""

import argparse
import json

def parse_global_lines(text_lines):
    """Search all lines of text for "GLOBAL". When the string is found in a
    line, parse the next line to identify the import.

    Assumes that "GLOBAL" string only appears inside an opcode name, and that
    the import line is of the form "from module import submodule".
    """

    globals_set = set()
    for i, line in enumerate(text_lines):
        if "GLOBAL" in line:
            next_line = text_lines[i + 1].strip()
            if next_line.startswith("from"):
                parts = next_line.split()
                module = parts[1]
                submodule = parts[3]
                globals_set.add(f"{module}.{submodule}")
    return list(globals_set)


def parse_reduce_lines(text_lines):
    """Search all lines of text for "REDUCE". When the string is found in a
    line, parse the next line to identify the called callable.

    Assumes that "REDUCE" string only appears inside an opcode name, and that
    the callable line is of the form "variable = callabe(args)"
    """

    reduce_set = set()
    for i, line in enumerate(text_lines):
        if "REDUCE" in line:
            next_line = text_lines[i + 1].strip()
            if '(' in next_line and ')' in next_line:
                function_call = next_line.split('=')[1].strip() if '=' in next_line else next_line
                function_name = function_call.split('(')[0].strip()
                reduce_set.add(function_name)
    return list(reduce_set)


def get_callable_name(fullname: str) -> str:
    return fullname.split('.')[-1]

def get_reduce_fullname(reduce_callable: str, global_callables:str ) -> str:
    try:
        indexof = list(map(get_callable_name, global_callables)).index(reduce_callable)
    except ValueError as err:
        return "builtins" + reduce_callable


    return global_callables[indexof]


def parse_trace_to_json(text_lines: str) -> str:
    """Take text input and parse all GLOBAL imports and REDUCE callables and
    return result as a JSON string.
    """

    globals_result = parse_global_lines(text_lines)
    reduce_result = parse_reduce_lines(text_lines)
    reduce_result_fullnames = [
        get_reduce_fullname(reduce_name, globals_result)
        for reduce_name in reduce_result
    ]


    output = {
        "globals": globals_result,
        "reduces": reduce_result_fullnames
    }

    return json.dumps(output, indent=2)

def main():
    """Read filename from command line and output all GLOBAL imports and REDUCE
    callables as JSON.
    """

    parser = argparse.ArgumentParser(
        description="Parse a file for GLOBAL and REDUCE lines.")
    parser.add_argument(
        'filename',
        type=str,
        help='The name of the file to process.')

    args = parser.parse_args()

    try:
        with open(args.filename, 'r', encoding='utf-8') as file:
            text_lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: The file '{args.filename}' was not found.")
        return

    print(parse_trace_to_json(text_lines))


if __name__ == "__main__":
    main()
