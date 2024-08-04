from modeltrace import trace_model, get_imports_from_trace, get_nonstandard_imports
import os
import logging
import csv
from tqdm import tqdm

PEATMOSS_PATH = os.getenv("PEATMOSS_PATH")
FILE_EXTENSIONS = ['.pkl', '.pt', '.pth', '.bin']

# Output directories and files
TRACE_DIR = "traces"
CSV_NONSTANDARD_OUTPUT = "nonstandard_imports.csv"
CSV_STANDARD_OUTPUT = "standard_imports.csv"

# Ensure the trace directory exists
os.makedirs(TRACE_DIR, exist_ok=True)


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


def find_pickle_file(directory: str):
    """
    Find and return the path of the first pickle file in the directory.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                return os.path.join(root, file)
    return None


def analyze_peatmoss(model_path: str) -> str:
    """
    Analyze the model using trace_model from modeltrace and return the trace.
    """
    logging.info("Analyzing model: %s", model_path)
    if not PEATMOSS_PATH:
        raise RuntimeError("PEATMOSS_PATH environment variable not set")
    return trace_model(model_path)


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Running Peatmoss analysis")

    if not PEATMOSS_PATH:
        raise RuntimeError("PEATMOSS_PATH environment variable not set")

    total_repos = count_model_repos(PEATMOSS_PATH)
    logging.info("Total model repositories to process: %d", total_repos)

    all_imports = []
    all_nonstandard_imports = []

    # Loop through the directories and find pickle files with tqdm progress bar
    for author, model, model_repo in tqdm(find_model_repo(PEATMOSS_PATH), total=total_repos, desc="Processing Repositories"):
        logging.info("Processing repository: %s", model_repo)
        pickle_file = find_pickle_file(model_repo)
        if pickle_file:
            logging.info("Found pickle file: %s", pickle_file)
            model_trace = analyze_peatmoss(pickle_file)

            # Save model trace to a file in the traces directory
            trace_filename = f"trace_{author}_{model}.txt"
            trace_filepath = os.path.join(TRACE_DIR, trace_filename)
            with open(trace_filepath, 'w') as f:
                f.write(model_trace)
            
            imports = get_imports_from_trace(model_trace)
            nonstandard_imports = get_nonstandard_imports(model_trace)
            all_imports.extend(imports)
            all_nonstandard_imports.extend(nonstandard_imports)
        else:
            logging.warning("No pickle file found in repository: %s", model_repo)

    # Save nonstandard imports to CSV
    with open(CSV_NONSTANDARD_OUTPUT, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Nonstandard Import'])
        
        for imp in all_nonstandard_imports:
            csvwriter.writerow([imp])

    # Save standard imports to CSV
    with open(CSV_STANDARD_OUTPUT, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Standard Import'])
        
        for imp in all_imports:
            csvwriter.writerow([imp])


if __name__ == '__main__':
    main()
