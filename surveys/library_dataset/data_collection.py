from huggingface_hub import HfApi, hf_hub_download
import os
import csv
import re
import requests
import ast
from loguru import logger
import time
from huggingface_hub.utils import HfHubHTTPError
from functools import wraps
from collections import defaultdict
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fetch tokens from environment variables
HF_TOKEN = os.environ.get('HF_TOKEN', None)
GH_TOKEN = os.environ.get('GITHUB_TOKEN', None)

# Set cache directory
CACHE_DIR = os.environ.get('PICKLE_CACHE', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

logger.add("data_collection.log", rotation="100 MB")
IGNORED_LIBRARIES = {
    'torch', 'transformers', 'tensorflow', 'urllib', 're', 'numpy', 'pandas',
    'matplotlib', 'requests', 'typing', 'PIL', 'asyncio', 'os', 'sys',
    'json', 'collections', 'logging', 'datasets', 'jax'
}

def retry_on_rate_limit(max_retries=13, base_delay=1, max_delay=3600):
    """
    Decorator to retry a function when rate limit is exceeded, using exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = base_delay
            while True:
                try:
                    return func(*args, **kwargs)
                except HfHubHTTPError as e:
                    if e.response is not None and e.response.status_code == 429:
                        retries += 1
                        if retries > max_retries:
                            logger.error(f"Exceeded maximum retries ({max_retries}) for function {func.__name__}")
                            raise
                        reset_time = e.response.headers.get('X-RateLimit-Reset')
                        if reset_time:
                            sleep_time = int(reset_time) - int(time.time())
                            sleep_time = max(sleep_time, delay)
                        else:
                            sleep_time = delay
                        sleep_time = min(sleep_time, max_delay)
                        logger.warning(f"Rate limit exceeded for {func.__name__}. Sleeping for {sleep_time} seconds (Retry {retries}/{max_retries}).")
                        time.sleep(sleep_time)
                        delay = min(delay * 2, max_delay)  # Exponential backoff with max delay
                    else:
                        logger.error(f"HTTP Error in function {func.__name__}: {e}")
                        raise
                except Exception as e:
                    logger.error(f"Error in function {func.__name__}: {e}")
                    raise
        return wrapper
    return decorator

@retry_on_rate_limit(max_retries=13, base_delay=1, max_delay=3600)
def get_pop_models(download_threshold=1000):
    """
    Get the list of popular models over a certain threshold on HuggingFace.
    """
    api = HfApi(token=HF_TOKEN)
    models = api.list_models(sort='downloads', direction=-1, full=True)  # Remove 'limit' after testing
    pop_models = [model for model in models if model.downloads and model.downloads >= download_threshold]
    logger.info(f"Found {len(pop_models)} popular models for analysis")
    return pop_models

@retry_on_rate_limit(max_retries=13, base_delay=1, max_delay=3600)
def get_model_card(model_id):
    """
    Get the model card of the model.
    """
    model_card_path = hf_hub_download(repo_id=model_id, filename='README.md', cache_dir=CACHE_DIR, token=HF_TOKEN)
    with open(model_card_path, 'r', encoding='utf-8') as f:
        model_card = f.read()
    return model_card

@retry_on_rate_limit(max_retries=13, base_delay=1, max_delay=3600)
def get_model_metadata(model_id):
    """
    Get the likes and downloads of the model.
    """
    api = HfApi(token=HF_TOKEN)
    model_info = api.model_info(model_id)
    likes = model_info.likes or 0
    downloads = model_info.downloads or 0
    return {'likes': likes, 'downloads': downloads}

def get_code_blocks(model_card):
    """
    Extract code blocks from the model card, regardless of language specified.
    Exclude code blocks that are likely to be BibTeX citations.
    """
    code_blocks = re.findall(r'```(?:\s*\w*\s*)\n(.*?)```', model_card, re.DOTALL)
    # Filter out code blocks that start with '@', which is typical for BibTeX entries
    code_blocks = [code for code in code_blocks if not code.strip().startswith('@')]
    return code_blocks

def get_imported_entities(code):
    """
    Extract imported entities (classes/functions) along with their full module paths.
    """
    imported_entities = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        logger.warning("Syntax error when parsing code block.")
        return imported_entities

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name  # e.g., 'torch'
                asname = alias.asname if alias.asname else alias.name
                top_level_module = module_name.split('.')[0]
                if top_level_module not in IGNORED_LIBRARIES:
                    imported_entities.append({
                        'library': top_level_module,
                        'module': module_name,
                        'name': None,
                        'asname': asname,
                        'full_name': module_name
                    })
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module  # e.g., 'optimum.onnxruntime'
            if module_name is None:
                continue  # Handle 'from . import X' cases
            top_level_module = module_name.split('.')[0]
            if top_level_module in IGNORED_LIBRARIES:
                continue
            for alias in node.names:
                name = alias.name  # e.g., 'ORTModelForFeatureExtraction'
                asname = alias.asname if alias.asname else alias.name
                full_name = f"{module_name}.{name}"
                imported_entities.append({
                    'library': top_level_module,
                    'module': module_name,
                    'name': name,
                    'asname': asname,
                    'full_name': full_name
                })
    return imported_entities

def process_model(model):
    """
    Process a single model to extract required information.
    """
    model_id = model.modelId
    logger.info(f"Processing model: {model_id}")

    # Initialize per-model data
    model_data = {}
    library_list = set()
    usage_code = ''
    imported_entities = []

    try:
        model_card = get_model_card(model_id)
    except Exception as e:
        logger.warning(f"Failed to get model card for {model_id}: {e}")
        return None
    if not model_card:
        logger.warning(f"Empty model card for {model_id}")
        return None

    code_blocks = get_code_blocks(model_card)
    if not code_blocks:
        logger.warning(f"No code blocks found for {model_id}")
        return None


    # Extract libraries and imported entities from code blocks
    for code in code_blocks:
        entities = get_imported_entities(code)
        imported_entities.extend(entities)
        for entity in entities:
            library_list.add(entity['library'])

    if not imported_entities:
        logger.warning(f"No relevant imports found in code blocks for {model_id}")
        return None

    try:
        metadata = get_model_metadata(model_id)
    except Exception as e:
        logger.warning(f"Failed to get metadata for {model_id}: {e}")
        return None
    likes = metadata.get('likes', 0)
    downloads = metadata.get('downloads', 0)

    # Combine all code blocks into intended usage
    usage_code = '\n\n'.join(code_blocks).strip()

    model_data['model_id'] = model_id
    model_data['libraries'] = list(library_list)
    model_data['likes'] = likes
    model_data['downloads'] = downloads
    model_data['intended_usage'] = usage_code
    model_data['imported_entities'] = imported_entities

    return model_data

def main():
    pop_models = get_pop_models()

    # Initialize data structures
    all_model_data = []
    libraries = set()
    library_to_models = defaultdict(list)
    library_to_entities = defaultdict(list)  # Map libraries to imported entities

    max_workers = 5  # Adjust based on your system and API limits
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_model, model): model for model in pop_models}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Models"):
            model_data = future.result()
            if model_data:
                all_model_data.append(model_data)
                # Update libraries and mappings
                for lib in model_data['libraries']:
                    lib = lib.strip()
                    libraries.add(lib)
                    library_to_models[lib].append(model_data['model_id'])
                for entity in model_data['imported_entities']:
                    library_to_entities[entity['library']].append({
                        'model_id': model_data['model_id'],
                        'module': entity.get('module'),
                        'name': entity.get('name'),
                        'full_name': entity.get('full_name', '')
                    })
            else:
                continue  # Skip if model_data is None

    # Prepare to write to CSV for model information
    with open('model_info.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['model_id', 'libraries', 'likes', 'downloads', 'imported_entities', 'intended_usage']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for model_data in all_model_data:
            # Format imported_entities as a string
            entities_str = '; '.join([e['full_name'] for e in model_data['imported_entities']])
            writer.writerow({
                'model_id': model_data['model_id'],
                'libraries': ', '.join(model_data['libraries']),
                'likes': model_data['likes'],
                'downloads': model_data['downloads'],
                'imported_entities': entities_str,
                'intended_usage': model_data['intended_usage']
            })

    # For library information, create a CSV file with headers
    with open('library_info.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['library_name', 'github_repo', 'stars', 'usage_count', 'model_ids', 'imported_entities']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        # Write libraries to CSV with models that use them and imported entities
        for library in sorted(libraries):
            model_ids = library_to_models[library]
            usage_count = len(model_ids)  # Number of models using the library
            entities = library_to_entities[library]
            # Format entities as a string
            entities_str = '; '.join([f"{e['model_id']}: {e['full_name']}" for e in entities])
            writer.writerow({
                'library_name': library,
                'github_repo': '',  # To be filled manually
                'stars': '',        # To be filled manually
                'usage_count': usage_count,
                'model_ids': ', '.join(model_ids),
                'imported_entities': entities_str
            })

if __name__ == "__main__":
    main()
