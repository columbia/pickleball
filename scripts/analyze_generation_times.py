import csv
import glob
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir_path = os.path.join(script_dir, "..", "results")
file_pattern = os.path.join(results_dir_path, "*.timelog")
log_files = glob.glob(file_pattern)

if not log_files:
    print(f"Error: No file found matching the pattern '{file_pattern}'")
else:
    filepath = log_files[0]

    try:
        with open(filepath, "r", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
            data = list(reader)

        all_content = [headers] + data
        num_columns = len(headers)
        col_widths = [0] * num_columns

        for row in all_content:
            for i, cell in enumerate(row):
                if len(cell) > col_widths[i]:
                    col_widths[i] = len(cell)

        def create_separator(char):
            return "+" + "+".join([char * (width + 2) for width in col_widths]) + "+"

        def format_row(row):
            cells = [f" {item:<{col_widths[i]}} " for i, item in enumerate(row)]
            return "|" + "|".join(cells) + "|"

        border = create_separator("-")
        header_separator = create_separator("=")

        print("PickleBall policy generation times:")
        print(border)
        print(format_row(headers))
        print(header_separator)

        for row in data:
            print(format_row(row))

        print(border)

    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
