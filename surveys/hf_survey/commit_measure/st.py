# Standard library imports
import json
import os
import subprocess
from datetime import datetime

# Related third party imports
from git import Repo
from git.exc import NoSuchPathError, InvalidGitRepositoryError
import matplotlib.pyplot as plt
import numpy as np
from huggingface_hub import HfApi, hf_hub_download
from loguru import logger
from tqdm import tqdm

# os.environ.pop('SSH_ASKPASS', None)
# Set the base directory for cloning
BASE_DIR = "/scratch/gilbreth/jiang784/safe-pickle"

def clone_repos(model_list, timeout=10): 
    """Clone repositories from a list of model names with a timeout."""
    for model in tqdm(model_list):
        repo_url = f"https://huggingface.co/{model.modelId}"
        repo_name = model.modelId.split('/')[-1]
        full_path = os.path.join(BASE_DIR, repo_name)
        if not os.path.exists(full_path):
            try:
                print(f"Attempting to clone {repo_url} into {full_path}...")
                # Using subprocess to execute the git clone command with a timeout
                subprocess.run(["git", "clone", repo_url, full_path], timeout=timeout, check=True)
                print(f"Successfully cloned {repo_name}")
            except subprocess.TimeoutExpired:
                print(f"Cloning {repo_name} timed out. It may require authentication. Skipping...")
            except Exception as e:
                print(f"An error occurred while cloning {repo_name}: {e}")
        else:
            print(f"Repository {repo_name} already exists at {full_path}.")


def get_first_commit_time(repo_path, file_extension):
    """Get the first commit time for files with a certain extension in a repository."""
    try:
        repo = Repo(repo_path)
        # Dynamically get the default branch name
        default_branch = repo.heads[0]  # This gets the first head as default, usually correct for single-branch repos
    except (InvalidGitRepositoryError, NoSuchPathError):
        print(f"Warning: '{repo_path}' is not a valid Git repository.")
        return None
    except IndexError:  # Catch empty repos with no heads
        print(f"Warning: '{repo_path}' has no branches.")
        return None

    first_time = None
    try:
        for commit in repo.iter_commits(rev=default_branch, paths=f'*{file_extension}', reverse=True):
            for item in commit.stats.files.keys():
                if item.endswith(file_extension):
                    first_time = commit.committed_datetime
                    return first_time  # Return the earliest commit time found
    except Exception as e:
        print(f"Error getting commit time for {file_extension} in {repo_path}: {e}")
    return first_time




def plot_results(commit_times):
    labels = ['Commited at the Same Time', 'Safetensor Commited After .bin', '.bin Commited After Safetensor', 'Safetensor Absent', '.bin Absent', 'Both Absent']
    counts = [0, 0, 0, 0, 0, 0]  # Initialize counts for each category

    # Calculate statistics based on commit times
    for times in commit_times.values():
        # Increment corresponding count based on commit time comparison
        if times['safetensor'] is None and times['bin'] is None:
            counts[5] += 1
        elif times['safetensor'] is None:
            counts[3] += 1
        elif times['bin'] is None:
            counts[4] += 1
        elif times['safetensor'] == times['bin']:
            counts[0] += 1
        elif times['safetensor'] > times['bin']:
            counts[1] += 1
        else:
            counts[2] += 1

    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(counts, startangle=90, autopct="")

    # Custom annotations
    total = sum(counts)
    for i, wedge in enumerate(wedges):
        percentage = 100.0 * counts[i] / total
        angle = (wedge.theta1 + wedge.theta2) / 2  # Middle of the wedge
        x = np.cos(np.deg2rad(angle))
        y = np.sin(np.deg2rad(angle))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = f"angle,angleA=0,angleB={angle}"
        ax.annotate(f'{percentage:.1f}%', xy=(0.6*x, 0.6*y), 
                    xytext=(1.2*x, 1.2*y),
                    horizontalalignment=horizontalalignment,
                    arrowprops=dict(arrowstyle="->", connectionstyle=connectionstyle))

    # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.axis('equal')

    # Adding legend outside of the plot
    plt.legend(wedges, labels, title="File Status", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    plt.savefig("commit_time_comparison.png", bbox_inches='tight')



def check_for_code(repo_path):
    """Check if the repository contains any .py files."""
    has_code = False
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.py'):
                has_code = True
                break  # Stop searching once a .py file is found
        if has_code:
            break  # Exit the outer loop as well
    return has_code



def main():
    api = HfApi()
    models = list(api.list_models(sort="downloads", direction=-1, limit=10000))

    model_commit_times = {}  # Dictionary to store first commit times and code presence

    # Ensure the base directory exists
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
        print(f"Created directory {BASE_DIR}")

    # Clone the model repositories
    # clone_repos(models)

    # Fetch and store first commit times for .safetensor and .bin files, and check for .py files
    for model in tqdm(models):
        full_model_id = model.modelId  # This includes both author and repository name
        repo_name = model.modelId.split('/')[-1]
        repo_path = os.path.join(BASE_DIR, repo_name)
        safetensor_time = get_first_commit_time(repo_path, '.safetensors')
        bin_time = get_first_commit_time(repo_path, '.bin')
        custom_code = check_for_code(repo_path)  # Check if .py files are present

        # Update the dictionary with all information
        model_commit_times[full_model_id] = {
            'safetensor': safetensor_time.isoformat() if safetensor_time else None,
            'bin': bin_time.isoformat() if bin_time else None,
            'custom_code': custom_code
        }
    
    # Save the results
    with open('model_commit_times.json', 'w') as f:
        json.dump(model_commit_times, f, indent=4)

    # Plot the results
    plot_results(model_commit_times)


if __name__ == "__main__":
    main()