from modeltrace import trace_model, get_imports_from_trace, get_nonstandard_imports
import os
import logging
import csv
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, TimeoutError

PEATMOSS_PATH = os.getenv("PEATMOSS_PATH")
FILE_EXTENSIONS = ['.pkl', '.pt', '.pth', '.bin']

# Output directories and files
TRACE_DIR = "traces"
CSV_OUTPUT = "imports.csv"
COMPLETED_LIST = "completed_repos.txt"
ABNORMAL_MODELS_LIST = "abnormal_models_list.txt"
TIMEOUT = 300  # 5 minutes

# Ensure the necessary directories and files exist
os.makedirs(TRACE_DIR, exist_ok=True)

def load_completed_list(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_completed_repo(repo, file_path):
    with open(file_path, 'a') as f:
        f.write(repo + '\n')

def find_model_repo(directory: str):
    """
    Generator function to find model repository directories.
    Yields each model repository directory found.
    """
    for initial in os.listdir(directory):
        initial_path = os.path.join(directory, initial)
        if os.path.isdir(initial_path):
            for author in os.listdir(initial_path):
                author_path = os.path.join(initial_path, author)
                if os.path.isdir(author_path):
                    for model in os.listdir(author_path):
                        model_path = os.path.join(author_path, model)
                        if os.path.isdir(model_path):
                            yield author, model, model_path

def count_model_repos(directory: str) -> int:
    """
    Count the total number of model repository directories.
    """
    count = 0
    for initial in os.listdir(directory):
        initial_path = os.path.join(directory, initial)
        if os.path.isdir(initial_path):
            for author in os.listdir(initial_path):
                author_path = os.path.join(initial_path, author)
                if os.path.isdir(author_path):
                    for model in os.listdir(author_path):
                        model_path = os.path.join(author_path, model)
                        if os.path.isdir(model_path):
                            count += 1
    return count

def find_pickle_files(directory: str):
    """
    Find and return the paths of all pickle files in the directory.
    """
    pickle_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                pickle_files.append(os.path.join(root, file))
    return pickle_files

def read_trace_file(filepath: str) -> str:
    with open(filepath, 'r') as f:
        return f.read()

def analyze_peatmoss(model_path: str) -> str:
    """
    Analyze the model using trace_model from modeltrace and return the trace.
    """
    logging.info("Analyzing model: %s", model_path)
    if not PEATMOSS_PATH:
        raise RuntimeError("PEATMOSS_PATH environment variable not set")
    return trace_model(model_path)

def analyze_with_timeout(model_path: str, timeout: int):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(analyze_peatmoss, model_path)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            return None

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Running Peatmoss analysis")

    if not PEATMOSS_PATH:
        raise RuntimeError("PEATMOSS_PATH environment variable not set")

    total_repos = count_model_repos(PEATMOSS_PATH)
    logging.info("Total model repositories to process: %d", total_repos)

    completed_repos = load_completed_list(COMPLETED_LIST)
    abnormal_models = load_completed_list(ABNORMAL_MODELS_LIST)

    # Write headers to the CSV file if it does not exist
    if not os.path.exists(CSV_OUTPUT):
        with open(CSV_OUTPUT, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Model Name', 'File Extension', 'Relative File Path', 'All Imports', 'Nonstandard Imports', 'Have Nonstandard Import'])

    # Loop through the directories and find pickle files with tqdm progress bar
    for author, model, model_repo in tqdm(find_model_repo(PEATMOSS_PATH), total=total_repos, desc="Processing Repositories"):
        repo_id = f"{author}/{model}"
        if repo_id in completed_repos or repo_id in abnormal_models:
            logging.info("Skipping completed or abnormal repository: %s", repo_id)
            continue

        logging.info("Processing repository: %s", model_repo)
        pickle_files = find_pickle_files(model_repo)
        if pickle_files:
            for pickle_file in pickle_files:
                logging.info("Found pickle file: %s", pickle_file)
                
                # Combine author and model name
                model_name = f"{author}/{model}"
                trace_filename = f"trace_{author}_{model}.txt"
                trace_filepath = os.path.join(TRACE_DIR, trace_filename)

                if os.path.exists(trace_filepath):
                    logging.info("Trace file already exists: %s", trace_filepath)
                    model_trace = read_trace_file(trace_filepath)
                else:
                    model_trace = analyze_with_timeout(pickle_file, TIMEOUT)
                    if model_trace is None:
                        logging.warning("Analysis timed out for model: %s", model_name)
                        save_completed_repo(repo_id, ABNORMAL_MODELS_LIST)
                        continue
                    with open(trace_filepath, 'w') as f:
                        f.write(model_trace)
                
                imports = get_imports_from_trace(model_trace)
                nonstandard_imports = get_nonstandard_imports(model_trace)
                
                all_imports_str = '\n'.join(imports)
                nonstandard_imports_str = '\n'.join(nonstandard_imports)
                have_nonstandard = 'True' if nonstandard_imports else 'False'

                # Calculate relative file path
                relative_file_path = os.path.relpath(pickle_file, start=model_repo)

                # Append imports to CSV
                with open(CSV_OUTPUT, 'a', newline='') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerow([model_name, os.path.splitext(pickle_file)[1], relative_file_path, all_imports_str, nonstandard_imports_str, have_nonstandard])

        else:
            logging.warning("No pickle file found in repository: %s", model_repo)

        # Save completed repository
        save_completed_repo(repo_id, COMPLETED_LIST)

if __name__ == '__main__':
    main()
