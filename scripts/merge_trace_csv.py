#!/usr/bin/env python3

"""Given a list of repositories and two CSVs files, select the rows from the
CSVs when the row has a repository in the list.

This whole thing would be so much easier if I had just used a database.
"""

import argparse
import csv

def parse_args():
    parser = argparse.ArgumentParser(description="Merge selected rows from two pipe-separated CSV files with no headers.")
    parser.add_argument("csv1", help="First input CSV file")
    parser.add_argument("csv2", help="Second input CSV file")
    parser.add_argument("keep_list", help="Text file listing row names to keep (one per line)")
    parser.add_argument("output", help="Output CSV file")
    return parser.parse_args()

def load_keep_list(path):
    with open(path, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def load_filtered_rows(csv_path, keep_names):
    filtered_rows = []
    with open(csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='|')
        for row in reader:
            if row and row[0] in keep_names:
                filtered_rows.append(row)
    return filtered_rows

def main():
    args = parse_args()

    keep_names = load_keep_list(args.keep_list)

    rows1 = load_filtered_rows(args.csv1, keep_names)
    rows2 = load_filtered_rows(args.csv2, keep_names)

    all_rows = rows1 + rows2
    all_rows.sort(key=lambda row: row[0])  # Sort by first column

    with open(args.output, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='|')
        writer.writerows(all_rows)

    print(f"Merged output written to {args.output}")

if __name__ == "__main__":
    main()
