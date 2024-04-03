import glob
import os
import re

import requests
from download_model import generate_trace, get_model_paths
from git import Repo
from torch.hub import _get_cache_or_reload, get_dir

TORCHHUB_REPO_GIT_URL = "https://github.com/pytorch/hub.git"
TMP_HUB_DIR = "/tmp/hub"

NOT_REPOS = ["README.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md"]
PATTERN = r"'https:\/\/[^']+\.(?:pt|pth)'|\"https:\/\/[^\"]+\.(?:pt|pth)\""


def download_hub_models():
    for repo_desc_filename in glob.glob(TMP_HUB_DIR + "/*.md"):
        if os.path.basename(repo_desc_filename) in NOT_REPOS:
            continue

        # Grab the github id from the description and download the repo
        with open(repo_desc_filename) as f:
            github_id = [x for x in f.read().split("\n") if x.startswith("github-id")][
                0
            ].split(": ")[1]

            _get_cache_or_reload(github_id, False, True, "download", True)


def download_additional_models():
    """Some projects download the actual model when they get loaded (e.g.,
    https://github.com/facebookresearch/WSL-Images/blob/main/hubconf.py).
    To avoid doing that, we do this hack where we look for urls each model's
    hubconf and just download the model from url"""

    hub_dir = get_dir()
    for hubconf_filename in glob.glob(hub_dir + "/**/hubconf.py"):
        with open(hubconf_filename) as f:
            lines = f.read().split("\n")
            for line in lines:
                matches = re.findall(PATTERN, line)
                if len(matches) > 0:
                    download_dir = os.path.dirname(hubconf_filename)
                for url in matches:
                    try:
                        url = url[1:-1]
                        response = requests.get(url)
                        if response.status_code == 200:
                            model_filename = download_dir + "/" + url.split("/")[-1]
                            with open(model_filename, "wb") as model_f:
                                print(f"Saving model at {model_filename}")
                                model_f.write(response.content)
                        else:
                            print(
                                f"Failed to download {url}: Status code {response.status_code}"
                            )
                    except Exception as e:
                        print(f"Error downloading {url}: {e}")


def process_models():
    """Generate the traces for the downloaded models"""

    model_paths = get_model_paths(get_dir())
    for model_path in model_paths:
        generate_trace(model_path)


if __name__ == "__main__":

    if not os.path.exists(TMP_HUB_DIR):
        Repo.clone_from(TORCHHUB_REPO_GIT_URL, TMP_HUB_DIR)

    download_hub_models()
    download_additional_models()

    process_models()
