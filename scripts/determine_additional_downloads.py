"""
Given a csv of repositories that we have already traced, and a list of new
repositories that we may or may not have traced, return the lists of
repositories that have already been traced and those that have not.
"""

import argparse
import csv
from typing import List, Dict

import process_csv

# Sample top 1665 models from total of 31637
# https://www.calculator.net/sample-size-calculator.html
def read_new_csv(csv_file, take_lines=1665) -> Dict[str, str]:

    new_models = {}
    with open(csv_file, 'r') as fd:
        analyzed_lines = csv.reader(fd, delimiter=',', quoting=csv.QUOTE_NONE)

        # Transform CVS into a list of tuples: (repo,#downloads)
        entries = [(row[0], int(row[1])) for row in analyzed_lines]

    # Order list of tuples by #downloads
    entries.sort(key=lambda row: row[1], reverse=True)

    # Return top n entries
    entries = entries[:take_lines]

    # Format into expected dictionary format
    return {key: value for (key, value) in entries}


# Get list of models already downloaded and traced
def repositories_to_process(downloaded_csv, new_models_csv) -> List[str]:

    print('reading existing models csv')
    traced_repos: Dict[str, process_csv.Repository] = process_csv.read_repos(downloaded_csv)

    print('reading new models csv')
    new_repos: Dict[str, str] = read_new_csv(new_models_csv)

    missing_models = set(new_repos.keys()) - set(traced_repos.keys())
    existing_models = set(new_repos.keys()).intersection(set(traced_repos.keys()))

    print(f'# traced models: {len(traced_repos.keys())}')
    print(f'# new models: {len(new_repos.keys())}')
    print(f'# missing models: {len(missing_models)}')
    print(missing_models)
    with open('missing_models', 'w') as fd:
        for element in missing_models:
            fd.write(element + '\n')

    print(f'# existing models: {len(existing_models)}')
    print(existing_models)
    with open('existing_models', 'w') as fd:
        for element in existing_models:
            fd.write(element + '\n')


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("downloaded_csv")
    parser.add_argument("new_models_csv")
    args = parser.parse_args()

    repositories_to_process(args.downloaded_csv, args.new_models_csv)

if __name__ == '__main__':
    main()
