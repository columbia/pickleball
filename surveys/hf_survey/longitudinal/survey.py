"""
    This script is used to create a survey for the Hugging Face longitudinal study.
    The survey includes the following datasets:
    - PTMTorrent
    - HFCommunity (dump_ files)
    - PeaTMOSS
    - ESEM
    - Aug 2024 (data_Socket_Aug)
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
    df = pd.read_csv(data_path, dtype={
        'tag_names': str,
        'filenames': str,
        'libraries': str,
        'model_id': str
    })
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

def extract_framework(input_data):
    known_frameworks = [
        'pytorch', 'tf', 'jax', 'safetensors',
        'onnx', 'tflite', 'keras', 'flax'
    ]

    # Ensure input_data is a Series
    if not isinstance(input_data, pd.Series):
        input_data = pd.Series(input_data)

    return [extract_framework_single(item, known_frameworks) for item in input_data]

def extract_framework_single(item, known_frameworks):
    item_list = []

    if isinstance(item, str):
        item = item.strip()
        if item.startswith('[') and item.endswith(']'):
            try:
                item_parsed = ast.literal_eval(item)
                if isinstance(item_parsed, list):
                    item_list.extend([str(t).lower() for t in item_parsed if not pd.isna(t)])
                else:
                    item_list.extend(item.lower().split(', '))
            except (SyntaxError, ValueError):
                item_list.extend(item.lower().split(', '))
        else:
            item_list.extend(item.lower().split(', '))
    elif isinstance(item, (list, np.ndarray)):
        item_list.extend([str(t).lower() for t in item if not pd.isna(t)])
    elif pd.isna(item):
        pass  # Do nothing for NaN
    else:
        logger.warning(
            f"Unexpected item type: {type(item)}. Value: {item}"
        )

    if not item_list:
        return set(['unknown'])

    frameworks = set(fw for fw in known_frameworks if fw in item_list)

    # Add 'others' if there are items not in known_frameworks
    if set(item_list) - set(known_frameworks):
        frameworks.add('others')

    return frameworks if frameworks else set(['unknown'])

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

def main() -> None:
    # Configure logging to show debug messages
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    all_data = load_data()
    data_frames = []

    for df in all_data:
        if df.empty:
            continue
        date = df['date'].iloc[0]  # Assuming all rows in a DataFrame have the same date

        # Prepare the input data by combining tags and libraries
        tags = df.get('tag_names', df.get('tag_name', df.get('tags', pd.Series(['']*len(df)))))
        libraries = df.get('libraries', pd.Series(['']*len(df)))
        input_data = tags if tags is not None else libraries

        # Extract frameworks and extensions
        frameworks_series = pd.Series(extract_framework(input_data))
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
            'frameworks': frameworks_series,
            'extensions': extensions_series,
            'date': date
        })

        data_frames.append(df_date)

    # Concatenate all data_frames
    full_data = pd.concat(data_frames, ignore_index=True)

    # Remove duplicates to ensure one entry per model per date
    full_data = full_data.drop_duplicates(subset=['model_id', 'date'])

    # Initialize variables for the plots
    dates = sorted(full_data['date'].unique())

    # For Figure 1
    others_no_safetensors_counts = []
    safetensors_counts = []

    # For Figure 2
    model_records = []

    # Group by model_id to track changes over time
    grouped = full_data.groupby('model_id')

    for model_id, group in grouped:
        group = group.sort_values('date')
        dates_model = group['date'].tolist()
        frameworks_list = group['frameworks'].tolist()
        extensions_list = group['extensions'].tolist()

        # Handle potential NaN values in extensions_list
        has_safetensors = [
            ('safetensors' in exts) if isinstance(exts, (set, list)) else False 
            for exts in extensions_list
        ]
        date_first_seen = dates_model[0]
        date_safetensors_first_seen = None
        for date, has_st in zip(dates_model, has_safetensors):
            if has_st:
                date_safetensors_first_seen = date
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

    # For Figure 2: Cumulative count of models that added .safetensors over time
    cumulative_models_added_safetensors = []
    for date in dates:
        count = (models_added_safetensors_df['date_safetensors_first_seen'] <= date).sum()
        cumulative_models_added_safetensors.append(count)

    # For Figure 1: Calculate counts per date
    for date in dates:
        df_date = full_data[full_data['date'] == date]

        # Models that use 'others' frameworks and don't have '.safetensors' files
        models_others_no_safetensors = df_date[
            (df_date['frameworks'].apply(lambda x: 'others' in x if isinstance(x, (set, list)) else False)) &
            (df_date['extensions'].apply(lambda x: 'safetensors' not in x if isinstance(x, (set, list)) else True))
        ]
        count_others_no_safetensors = len(models_others_no_safetensors['model_id'].unique())
        others_no_safetensors_counts.append(count_others_no_safetensors)

        # Models that have '.safetensors' files
        models_with_safetensors = df_date[
            df_date['extensions'].apply(lambda x: 'safetensors' in x if isinstance(x, (set, list)) else False)
        ]
        count_models_with_safetensors = len(models_with_safetensors['model_id'].unique())
        safetensors_counts.append(count_models_with_safetensors)

    # Plot Figure 1
    plt.figure(figsize=(12, 6))
    plt.plot(dates, others_no_safetensors_counts, marker='o', label='Without .safetensors')
    plt.plot(dates, safetensors_counts, marker='o', label='With .safetensors')
    plt.title('Models Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Models')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('models_over_time.png')
    plt.close()

    # Plot Figure 2
    plt.figure(figsize=(12, 6))
    plt.plot(dates, cumulative_models_added_safetensors, marker='o', label='Models that added .safetensors')
    plt.title('Models Adding .safetensors Over Time')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Number of Models')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('models_added_safetensors.png')
    plt.close()

if __name__ == "__main__":
    main()
