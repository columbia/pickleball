"""
    This script is used to create a survey for the Hugging Face longitudinal study.
    The survey includes the following datasets:
    - PTMTorrent
    - HFCommunity
    - PeaTMOSS
    - ESEM
    - Aug 2024
    - Oct 2024
"""

import os
import sys
import json
import ast
import pandas as pd
import numpy as np
from collections import Counter
from loguru import logger
import matplotlib.pyplot as plt
from datetime import datetime

def load_ptmtorrent_data(data_path: str) -> pd.DataFrame:
    with open(data_path, 'r') as file:
        data = json.load(file)

    filtered_data = []
    for item in data:
        # Extract filenames from siblings
        siblings = item.get('siblings', [])
        filenames = ', '.join([sibling.get('rfilename', '') for sibling in siblings])
        filtered_data.append({
            "model_id": item.get("modelId", item.get("id", "")),
            "tags": item.get("tags", []),
            "downloads": item.get('downloads', 0),
            "filenames": filenames,
            "libraries": item.get('libraries', []),
            "date": datetime(2023, 1, 1)  # Set the date to January 2023 for PTMTorrent data
        })

    df = pd.DataFrame(filtered_data)
    df = df.sort_values('downloads', ascending=False).head(100000)

    return df

def load_hfcommunity_data(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path, dtype={'tag_names': str, 'filenames': str, 'libraries': str, 'model_id': str})
    df = df.sort_values('downloads', ascending=False).head(100000)

    # Parse the libraries column
    if 'libraries' in df.columns:
        df['libraries'] = parse_libraries_column(df['libraries'])

    # Extract date from filename
    filename = os.path.basename(data_path)
    date_str = filename.split('_')[1].split('.')[0]

    # Hardcoded date conversions
    date_mapping = {
        '241122': datetime(2022, 11, 24),
        '051523': datetime(2023, 5, 15),
        '090323': datetime(2023, 3, 9),
        '180423': datetime(2023, 4, 18),
        '20230630': datetime(2023, 6, 30),
        '20230812': datetime(2023, 8, 12),
        '20230907': datetime(2023, 9, 7),
        '20231009': datetime(2023, 10, 9)
    }

    date = date_mapping.get(date_str)

    if date is None:
        logger.error(f"Unable to parse date from filename: {filename}")

    df['date'] = date

    return df

def load_data_socket_aug(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path, dtype={
        'tag_names': str,
        'filenames': str,
        'siblings': str,
        'libraries': str,
        'context_id': str  # Use 'context_id' for data_Socket_Aug
    })
    df = df.sort_values('downloads', ascending=False).head(100000)
    df['date'] = datetime(2024, 8, 1)

    # Extract filenames from the 'siblings' column
    df['filenames'] = df['siblings'].apply(extract_filenames_from_siblings)

    # Parse the libraries column
    if 'libraries' in df.columns:
        df['libraries'] = parse_libraries_column(df['libraries'])

    # Rename 'context_id' to 'model_id' for consistency
    df.rename(columns={'context_id': 'model_id'}, inplace=True)

    return df

def load_data() -> list:
    data_Aug24 = load_data_socket_aug("./data/data_Socket_Aug.csv")

    data_ptmtorrent = load_ptmtorrent_data("./data/PTMTorrent.json")

    data_files = [
        f for f in os.listdir('./data')
        if f.startswith('dump_') and f.endswith('.csv')
    ]
    data_hfcommunity = []

    for file in data_files:
        data = load_hfcommunity_data(f"./data/{file}")
        data_hfcommunity.append(data)

    # Combine all data into a single list
    all_data = [data_Aug24, data_ptmtorrent] + data_hfcommunity

    return all_data

def parse_libraries_column(series):
    def parse_libraries(s):
        if pd.isna(s):
            return []
        if isinstance(s, str):
            s = s.strip()
            if s.startswith('[') and s.endswith(']'):
                try:
                    return ast.literal_eval(s)
                except (SyntaxError, ValueError):
                    return s.split(', ')
            else:
                return s.split(', ')
        elif isinstance(s, (list, np.ndarray)):
            return s
        else:
            return []
    return series.apply(parse_libraries)

def extract_filenames_from_siblings(siblings_str):
    if pd.isna(siblings_str):
        return ''
    try:
        # Try to parse as JSON first
        siblings_list = json.loads(siblings_str)
    except json.JSONDecodeError as e_json:
        # If JSON parsing fails, try to evaluate as a Python literal
        try:
            siblings_list = ast.literal_eval(siblings_str)
        except (SyntaxError, ValueError) as e_ast:
            logger.warning(
                f"Failed to parse siblings_str: JSON error: {e_json}. AST error: {e_ast}"
            )
            logger.debug(f"Problematic siblings_str: {siblings_str[:100]}...")
            return ''
    # Extract filenames
    filenames = ', '.join([
        sibling.get('rfilename', '') for sibling in siblings_list
        if isinstance(sibling, dict)
    ])
    return filenames

def extract_extensions(filenames_series, known_extensions):
    extensions_list = []
    for filenames in filenames_series:
        if pd.isna(filenames):
            extensions_list.append(set())
            continue
        filenames_list = filenames.split(', ')
        extensions = set()
        for filename in filenames_list:
            ext = os.path.splitext(filename)[1]  # includes the dot
            if ext.startswith('.'):
                ext = ext[1:]  # Remove the dot
            ext = ext.lower()
            if ext in known_extensions:
                extensions.add(ext)
        extensions_list.append(extensions)
    return extensions_list

def analysis_extensions(data: pd.DataFrame) -> pd.Series:
    filenames = data.get('filenames', data.get('filename'))
    if filenames is None:
        return pd.Series([set()]*len(data))
    known_extensions = [
        'bin', 'h5', 'hdf5', 'ckpt', 'pkl', 'pickle', 'dill',
        'pth', 'pt', 'model', 'pb', 'joblib', 'npy', 'npz',
        'safetensors', 'onnx'
    ]
    extensions_list = extract_extensions(filenames, known_extensions)
    return pd.Series(extensions_list)

def analysis_tags(data: pd.DataFrame) -> Counter:
    tag_names = data.get('tag_names', data.get('tag_name', data.get('tags')))
    if tag_names is None:
        return Counter()
    tags_list = []
    for tags in tag_names:
        if isinstance(tags, float) and pd.isna(tags):
            continue
        if isinstance(tags, str):
            tags_split = tags.split(', ')
            tags_list.extend(tags_split)
        elif isinstance(tags, (list, np.ndarray)):
            tags_list.extend(tags)
        else:
            logger.warning(
                f"Unexpected tag type in tags: {type(tags)}. Value: {tags}"
            )
    # Count
    tags_flat = [tag.lower() for tag in tags_list if tag and not pd.isna(tag)]
    tags_counter = Counter(tags_flat)
    return tags_counter


def plot_extensions_usage(extensions_usage: dict):
    dates = sorted(extensions_usage.keys())
    known_extensions = [
        'bin', 'h5', 'hdf5', 'ckpt', 'pkl', 'pickle',
        'dill', 'pth', 'pt', 'model', 'pb', 'joblib',
        'npy', 'npz', 'safetensors', 'onnx'
    ]
    extension_counts = {ext: [] for ext in known_extensions}

    for date in dates:
        date_usage = extensions_usage[date]
        for ext in known_extensions:
            count = date_usage.get(ext, 0)
            extension_counts[ext].append(count)

    plt.figure(figsize=(12, 6))
    for ext in known_extensions:
        plt.plot(
            dates, extension_counts[ext],
            marker='o', label=ext
        )

    plt.title('File Extensions Usage Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Models')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('extensions_usage.png')
    plt.close()


def plot_safetensors_usage(safetensors_usage: dict):
    dates = sorted(safetensors_usage.keys())
    counts = []

    for date in dates:
        count = safetensors_usage[date]
        counts.append(count)

    plt.figure(figsize=(12, 6))
    plt.plot(
        dates, counts,
        marker='o', label='Models with .safetensors Files'
    )

    plt.title('Usage of .safetensors Files Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Models')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('safetensors_usage.png')
    plt.close()

def plot_models_added_safetensors(dates, cumulative_counts):
    plt.figure(figsize=(12, 6))
    plt.plot(dates, cumulative_counts, marker='o', label='Models that added .safetensors')
    plt.title('Models Adding .safetensors Over Time')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Number of Models')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('models_added_safetensors.png')
    plt.close()

def main() -> None:
    # Configure logging to show debug messages
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    all_data = load_data()
    extensions_usage = {}
    tags_usage = {}
    safetensors_usage = {}

    data_frames = []

    for df in all_data:
        if df.empty:
            continue
        date = df['date'].iloc[0]  # Assuming all rows in a DataFrame have the same date

        # Prepare the input data by combining tags and libraries
        tags = df.get('tag_names', df.get('tag_name', df.get('tags', pd.Series(['']*len(df)))))
        libraries = df.get('libraries', pd.Series(['']*len(df)))
        input_data = tags if tags is not None else libraries

        # Extract extensions
        extensions_series = pd.Series(extract_extensions(df.get('filenames', pd.Series(['']*len(df))), known_extensions=[
            'bin', 'h5', 'hdf5', 'ckpt', 'pkl', 'pickle', 'dill',
            'pth', 'pt', 'model', 'pb', 'joblib', 'npy', 'npz',
            'safetensors', 'onnx'
        ]))

        # Determine the correct model identifier column
        if 'model_id' in df.columns:
            model_ids = df['model_id']
        elif 'modelId' in df.columns:
            model_ids = df['modelId']
        elif 'context_id' in df.columns:
            model_ids = df['context_id']
        else:
            logger.warning("No model identifier column found. Skipping this dataset.")
            continue

        # Create a DataFrame for the current date
        df_date = pd.DataFrame({
            'model_id': model_ids,
            'extensions': extensions_series,
            'date': date
        })

        data_frames.append(df_date)

        # Collect extension usage data
        extension_counter = Counter()
        for exts in extensions_series:
            for ext in exts:
                extension_counter[ext] += 1
        extensions_usage[date] = extension_counter

        # Analyze models with '.safetensors' files
        count_safetensors_files = sum('safetensors' in exts for exts in extensions_series)
        safetensors_usage[date] = count_safetensors_files

        # Analyze tags
        tags_counter = analysis_tags(df)
        tags_usage[date] = tags_counter

    # Concatenate all data_frames
    full_data = pd.concat(data_frames, ignore_index=True)

    # Remove duplicates to ensure one entry per model per date
    full_data = full_data.drop_duplicates(subset=['model_id', 'date'])

    # Initialize variables for the new figure
    dates = sorted(full_data['date'].unique())

    # For the new figure: Models that added .safetensors over time
    model_records = []

    # Group by model_id to track changes over time
    grouped = full_data.groupby('model_id')

    for model_id, group in grouped:
        group = group.sort_values('date')
        dates_model = group['date'].tolist()
        extensions_list = group['extensions'].tolist()

        # Determine if the model added .safetensors files after initial date
        has_safetensors = [
            ('safetensors' in exts) if isinstance(exts, (set, list)) else False
            for exts in extensions_list
        ]
        date_first_seen = dates_model[0]
        date_safetensors_first_seen = None
        for date_i, has_st in zip(dates_model, has_safetensors):
            if has_st:
                date_safetensors_first_seen = date_i
                break  # First occurrence of .safetensors

        model_records.append({
            'model_id': model_id,
            'date_first_seen': date_first_seen,
            'date_safetensors_first_seen': date_safetensors_first_seen
        })

    # Create DataFrame from model_records
    model_records_df = pd.DataFrame(model_records)

    # Identify models that did not have .safetensors at first but added it later
    models_added_safetensors_df = model_records_df[
        (model_records_df['date_safetensors_first_seen'].notna()) &
        (model_records_df['date_safetensors_first_seen'] > model_records_df['date_first_seen'])
    ]

    # For the new figure: Cumulative count of models that added .safetensors over time
    cumulative_models_added_safetensors = []
    for date in dates:
        count = (models_added_safetensors_df['date_safetensors_first_seen'] <= date).sum()
        cumulative_models_added_safetensors.append(count)

    # Plot Extensions Usage
    plot_extensions_usage(extensions_usage)

    # Plot .safetensors Usage
    plot_safetensors_usage(safetensors_usage)

    # Plot Models Adding .safetensors Over Time
    plot_models_added_safetensors(dates, cumulative_models_added_safetensors)

if __name__ == "__main__":
    main()
