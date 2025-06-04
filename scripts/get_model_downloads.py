#!/usr/bin/env python3

"""
Given a repository or list of repositories, get download counts.
"""

import argparse

import huggingface_hub
import huggingface_hub.hf_api

from typing import Tuple

def get_modelinfo(repo: str) -> huggingface_hub.hf_api.ModelInfo :
    return huggingface_hub.HfApi().model_info(repo)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository",
        help="Name of Hugging Face repository to fetch"
    )

    parser.add_argument(
        "--repositories-list",
        help="File with list of Hugging Face repositories"
    )
    args = parser.parse_args()

    if args.repository:
        repositories = [args.repository]

    elif args.repositories_list:
        repositories = []
        with open(args.repositories_list, 'r') as fd:
            for line in fd:
                repositories.append(line.strip())
    else:
        raise RuntimeError("Must provide --repostory or --repositories-list")

    total = 0
    for repository in repositories:
        model = get_modelinfo(repository)
        total += model.downloads
        print(repository, model.downloads)
        # model.downloads_all_time returns None for all models

    print(f'total: {total}')
