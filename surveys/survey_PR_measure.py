from huggingface_hub import HfApi, get_repo_discussions
import os
import time
from tqdm import tqdm
from functools import wraps
import csv
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
# Fetch HF token from environment variables
HF_TOKEN = os.environ.get('HF_TOKEN', None)

def check_sfconvertbot_prs(model_id):
    """
    Check if a model repository has PRs from SFconvertbot and their merge status.
    Returns a tuple of (has_sfconvert_prs, has_merged_prs, has_open_prs, discussions_disabled).
    """
    try:
        discussions_disabled = False
        try:
            discussions = get_repo_discussions(
                repo_id=model_id,
                discussion_type="pull_request",
                repo_type="model",
                token=HF_TOKEN
            )
        except Exception as e:
            if "403 Forbidden: Discussions are disabled for this repo" in str(e):
                discussions_disabled = True
                return (False, False, False, True)
            raise

        has_sfconvert_prs = False
        has_merged_prs = False
        has_open_prs = False
        
        for discussion in discussions:
            # logger.debug(f"PR for {model_id}: #{discussion.num} by {discussion.author}")
            if discussion.author == "SFconvertbot":
                has_sfconvert_prs = True
                if discussion.status == "merged":
                    has_merged_prs = True
                elif discussion.status == "open":
                    has_open_prs = True

        # logger.debug(f"Model {model_id} - Has SFconvertbot PRs: {has_sfconvert_prs}, Merged: {has_merged_prs}, Open: {has_open_prs}, Disabled: {discussions_disabled}")
        return (has_sfconvert_prs, has_merged_prs, has_open_prs, discussions_disabled)
    except Exception as e:
        print(f"Error checking PRs for {model_id}: {e}")
        raise

def load_unloadable_models():
    """
    Load the list of unloadable models from unloadable.txt
    """
    unloadable = set()
    try:
        with open('hf_survey/download_measure/unloadable.txt', 'r') as f:
            for line in f:
                if line.strip():
                    model_id = line.split()[0]  # Split by space and take first part
                    unloadable.add(model_id)
    except FileNotFoundError:
        print("Warning: unloadable.txt not found")
    return unloadable

def process_model(model_id):
    """
    Process a single model and return its results.
    """
    try:
        pr_status = check_sfconvertbot_prs(model_id)
        if pr_status is not None:
            has_sfconvert, has_merged, has_open, discussions_disabled = pr_status
            return model_id, has_sfconvert, has_merged, has_open, discussions_disabled, False  # False for not_found
    except Exception as e:
        if "404" in str(e):
            logger.warning(f"Repository not found: {model_id}")
            return model_id, False, False, False, False, True  # True for not_found
        if "403" in str(e):
            logger.warning(f"Discussions are disabled for {model_id}")
            return model_id, False, False, False, True, False  # True for discussions_disabled
    return None

def main():
    # Load unloadable models
    unloadable_models = load_unloadable_models()
    
    # Read models from CSV
    models_to_check = []
    with open('./paper_survey_1664.csv', 'r') as f:
        csv_reader = csv.reader(f, delimiter='|')
        for row in csv_reader:
            model_id = row[0].strip()
            if model_id not in unloadable_models:
                models_to_check.append(model_id)
    
    # Initialize counters
    total_models = len(models_to_check)  # Changed: Set total_models to actual total
    models_with_sfconvert = 0
    models_with_merged_prs = 0
    models_with_open_prs = 0
    models_discussions_disabled = 0
    models_not_found = 0
    results = []

    # Process models using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_model = {executor.submit(process_model, model_id): model_id 
                          for model_id in models_to_check}
        
        for future in tqdm(concurrent.futures.as_completed(future_to_model), 
                          total=len(models_to_check), 
                          desc="Checking repositories"):
            result = future.result()
            if result is not None:
                model_id, has_sfconvert, has_merged, has_open, discussions_disabled, not_found = result
                if not_found:
                    models_not_found += 1
                if discussions_disabled:
                    models_discussions_disabled += 1
                if has_sfconvert:
                    models_with_sfconvert += 1
                if has_merged:
                    models_with_merged_prs += 1
                if has_open:
                    models_with_open_prs += 1
                results.append(f"{model_id}\t{has_sfconvert}\t{has_merged}\t{has_open}\t{discussions_disabled}\t{not_found}")
            time.sleep(0.1)  # Small delay to avoid overwhelming the API

    # Write detailed results to file
    with open('sfconvert_results.txt', 'w') as f:
        f.write("Model ID | Has SFconvert PRs | Has Merged PRs | Has Open PRs | Discussions Disabled | Not Found\n")
        f.write("-" * 100 + "\n")
        for line in results:
            f.write(f"{line.replace('\t', ' | ')}\n")
        
        # Write summary statistics
        f.write("\nSummary Statistics:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Total models checked: {total_models}\n")
        f.write(f"Repositories not found: {models_not_found} ({models_not_found/total_models*100:.2f}%)\n")
        f.write(f"Models with discussions disabled: {models_discussions_disabled} ({models_discussions_disabled/total_models*100:.2f}%)\n")
        f.write(f"Models with SFconvertbot PRs: {models_with_sfconvert} ({models_with_sfconvert/total_models*100:.2f}%)\n")
        f.write(f"Models with merged PRs: {models_with_merged_prs} ({models_with_merged_prs/total_models*100:.2f}%)\n")
        f.write(f"Models with open PRs: {models_with_open_prs} ({models_with_open_prs/total_models*100:.2f}%)\n")

if __name__ == "__main__":
    main()