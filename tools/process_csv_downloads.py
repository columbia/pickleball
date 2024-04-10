import argparse
from typing import Dict

import huggingface_hub.hf_api

import download_model # Use get_model_info() for huggingface_hub.hf_api.ModelInfo object
import process_csv


def without_keys(d, keys):
    return {k: d[k] for k in d.keys() - keys}

def with_keys(d, keys):
    return {k: d[k] for k in keys}

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    parser.add_argument("--saved-values", default=False)
    args = parser.parse_args()

    repos: Dict[str, process_csv.Repository] = process_csv.read_repos(args.csv_file)
    repos = without_keys(repos, process_csv.failed_downloads(repos))

    downloads: Dict[str, int] = {}

    if not args.saved_values:
        for repo_name in repos:
            model_info: huggingface_hub.hf_api.ModelInfo = download_model.get_model_info(repo_name)
            downloads[repo_name] = model_info.downloads
        # Save downloads to disk for quick lookup later
        with open(args.csv_file + '.downloads', 'w') as downloads_csvfile:
            for k, v in downloads.items():
                downloads_csvfile.write(f'{k},{v}\n')

    else:
        # read saved-values CSV from disk
        with open(args.saved_values, 'r') as downloads_csvfile:
            for row in downloads_csvfile:
                row = row.split(',')
                downloads[row[0]] = int(row[1])

    total_repo_downloads = sum(downloads.values())

    violating_repos = [x[0] for x in process_csv.violating_models(repos)]
    # This is the number of downloads of repositories that contain any model with
    # 'unsafe' imports in a pickle program. This can include training_args, even
    # if the pytorch_model.bin does not contain additional imports.
    unsafe_repo_downloads = sum(with_keys(downloads, violating_repos).values())

    violating_repos_pytorch = [x[0] for x in process_csv.violating_models_pytorch(process_csv.violating_models(repos))]
    # This is the number of downloads of repositories that contain a
    # pytorch_model.bin model that contains additional 'unsafe' imports.
    unsafe_pytorch_repo_downloads = sum(with_keys(downloads, violating_repos_pytorch).values())

    print(f'total downloads: {total_repo_downloads}')
    print(f'unsafe downloads: {unsafe_repo_downloads} ({(unsafe_repo_downloads / total_repo_downloads) * 100:.2f}%)')
    print(f'unsafe pytorch downloads: {unsafe_pytorch_repo_downloads} ({(unsafe_pytorch_repo_downloads / total_repo_downloads) * 100:.2f}%)')

if __name__ == '__main__':
    main()