import os
import re
import sys
import json
import ast
import pandas as pd
import numpy as np
from collections import Counter
from loguru import logger
import matplotlib.pyplot as plt
from datetime import datetime

DOWNLOAD_THRESHOLD = 1000

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
            "downloads": item.get('downloads', 0),  # Use 'weekly_downloads' for PTMTorrent
            "filenames": filenames,
            "libraries": item.get('libraries', []),
            "date": datetime(2023, 1, 1)  # Set the date to January 2023 for PTMTorrent data
        })

    df = pd.DataFrame(filtered_data)
    df = df[df['downloads'] > DOWNLOAD_THRESHOLD]  # Filter models with over 100 downloads

    return df   

def load_hfcommunity_data(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path, dtype={'tag_names': str, 'filenames': str, 'libraries': str, 'model_id': str})
    df = df[df['downloads'] > DOWNLOAD_THRESHOLD]  # Filter models with over 100 downloads

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

def load_data_socket(data_path: str, date: datetime) -> pd.DataFrame:
    df = pd.read_csv(data_path, dtype={
        'tag_names': str,
        'filenames': str,
        'siblings': str,
        'libraries': str,
        'context_id': str  # Use 'context_id' for data_Socket files
    })
    df = df[df['downloads'] > DOWNLOAD_THRESHOLD]  # Filter models with over 100 downloads
    df['date'] = date

    # Extract filenames from the 'siblings' column
    df['filenames'] = df['siblings'].apply(extract_filenames_from_siblings)

    # Parse the libraries column
    if 'libraries' in df.columns:
        df['libraries'] = parse_libraries_column(df['libraries'])

    # Rename 'context_id' to 'model_id' for consistency
    df.rename(columns={'context_id': 'model_id'}, inplace=True)

    # Add category column based on file extensions
    def categorize_model(extensions):
        if not extensions:  # Empty set means no files
            return 'no_model_files'
        
        pickle_variants = {'pkl', 'pickle', 'joblib', 'dill'}
        pytorch_variants = {'pt', 'pth', 'bin'}
        model_extensions = pickle_variants | pytorch_variants | {'safetensors', 'onnx', 'h5', 'hdf5', 'ckpt', 'pb', 'model', 'npy', 'npz', 'msgpack', 'nemo', 'wav', 'gguf', 'keras', 'llamafile'}
        
        has_pickle = any(ext in pickle_variants for ext in extensions)
        has_pytorch = any(ext in pytorch_variants for ext in extensions)
        has_safetensors = 'safetensors' in extensions
        has_any_model_ext = any(ext in model_extensions for ext in extensions)
        
        if not has_any_model_ext:
            return 'no_model_files'  # No known model extensions found
        elif has_pickle:
            return 'pickle_variant_with_safetensors' if has_safetensors else 'pickle_variant_without_safetensors'
        elif has_pytorch:
            return 'pytorch_variant_with_safetensors' if has_safetensors else 'pytorch_variant_without_safetensors'
        elif has_safetensors:
            return 'only_safetensors'
        else:
            return 'other_formats'  # Has model files but in other formats (not pickle/pytorch/safetensors)

    # Extract extensions and create category column
    df['extensions'] = df['filenames'].apply(lambda x: {
        os.path.splitext(f)[1].lower().lstrip('.') 
        for f in x.split(', ') if f
    })
    df['model_category'] = df['extensions'].apply(categorize_model)

    return df

def load_data() -> list:
    data_Aug24 = load_data_socket("./data/data_Socket_Aug.csv", datetime(2024, 8, 1))
    data_Nov24 = load_data_socket("./data/data_Socket_Nov.csv", datetime(2024, 11, 15))
    data_Mar25 = load_data_socket("./data/data_Socket_Mar25.csv", datetime(2025, 3, 17))

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
    all_data = [data_Aug24, data_Nov24, data_Mar25, data_ptmtorrent] + data_hfcommunity

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
    unknown_extensions = Counter()  # Track unknown extensions
    
    # Regex to match valid extensions (e.g., alphanumeric, 1-5 chars, excludes numbers and symbols)
    valid_ext_pattern = re.compile(r'^[a-zA-Z]{1,5}$')

    for filenames in filenames_series:
        if pd.isna(filenames):
            extensions_list.append(set())
            continue
        filenames_list = filenames.split(', ')
        extensions = set()
        for filename in filenames_list:
            ext = os.path.splitext(filename)[1].lower().lstrip('.')  # Get extension, remove leading dot
            
            # Check for valid and known extensions only
            if ext in known_extensions:
                extensions.add(ext)
            elif valid_ext_pattern.match(ext):  # Only include valid alphanumeric extensions
                unknown_extensions[ext] += 1
        extensions_list.append(extensions)

    # Log or return unknown extensions to analyze later
    logger.info(f"Unknown extensions and counts: {unknown_extensions}")
    
    return extensions_list, unknown_extensions

def extract_relevant_extensions(filenames_series, model_names, relevant_extensions):
    extensions_list = []

    for filenames, model_name in zip(filenames_series, model_names):
        if pd.isna(filenames):
            extensions_list.append(set())
            continue

        filenames_list = filenames.split(', ')
        extensions = set()
        has_relevant_extension = False

        for filename in filenames_list:
            ext = os.path.splitext(filename)[1].lower().lstrip('.')  # Get extension without dot

            # Check if the extension is relevant
            if ext in relevant_extensions:
                extensions.add(ext)
                has_relevant_extension = True

        extensions_list.append(extensions)
    return extensions_list


def analysis_extensions(data: pd.DataFrame) -> pd.Series:
    filenames = data.get('filenames', data.get('filename'))
    if filenames is None:
        return pd.Series([set()]*len(data))
    known_extensions = [
        'bin', 'h5', 'hdf5', 'ckpt', 'pkl', 'pickle', 'dill',
        'pth', 'pt', 'model', 'pb', 'joblib', 'npy', 'npz',
        'safetensors', 'onnx', 'msgpack', 'nemo', 'wav', 'gguf', 'keras', 'llamafile'
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


def plot_pickle_downloads(data: pd.DataFrame, show_labels: bool = True):
    # Define pickle formats
    pickle_formats = {'pkl', 'pickle', 'joblib', 'dill', 'pt', 'pth', 'bin'}
    safetensors_format = 'safetensors'

    # Initialize lists for data
    dates = []
    pickle_models = []
    pickle_no_safe_models = []
    safetensors_only_models = []  # New list for safetensors-only models
    pickle_downloads = []
    pickle_no_safe_downloads = []
    safetensors_only_downloads = []  # New list for safetensors-only downloads
    total_models_per_date = []  # Store total model count per date

    # Process data by date
    for date in sorted(data['date'].unique()):
        subset = data[data['date'] == date]
        total_models = len(subset)  # Count total models for this date
        total_models_per_date.append(total_models)
        
        # Count models and downloads with pickle formats
        pickle_mask = subset['extensions'].apply(
            lambda exts: any(ext in pickle_formats for ext in exts))
        pickle_no_safe_mask = subset['extensions'].apply(
            lambda exts: any(ext in pickle_formats for ext in exts) 
            and safetensors_format not in exts)
        safetensors_only_mask = subset['extensions'].apply(
            lambda exts: safetensors_format in exts
            and not any(ext in pickle_formats for ext in exts))

        dates.append(date)
        pickle_models.append(sum(pickle_mask))
        pickle_no_safe_models.append(sum(pickle_no_safe_mask))
        safetensors_only_models.append(sum(safetensors_only_mask))  # Add safetensors-only count
        pickle_downloads.append(subset[pickle_mask]['downloads'].sum())
        pickle_no_safe_downloads.append(subset[pickle_no_safe_mask]['downloads'].sum())
        safetensors_only_downloads.append(subset[safetensors_only_mask]['downloads'].sum())  # Add safetensors-only downloads

    # Print the total population size for each date
    print("\nTotal population size (number of models) for each date:")
    for i, date in enumerate(dates):
        print(f"{date.strftime('%Y-%m-%d')}: {total_models_per_date[i]:,} models")
    print()

    if show_labels:
        # Use the correct date that matches your March dataset
        mar25_data = data[data['date'] == pd.Timestamp('2025-03-17')]
        
        # Use the intended pickle formats
        pickle_formats = ['pt', 'bin', 'ckpt', 'pth', 'h5', 'model', 'pkl']
        safetensors_format = 'safetensors'
        
        pickle_only_models = []
        pickle_only_downloads = []  # New list to store downloads
        for _, row in mar25_data.iterrows():
            # Ensure extensions is treated as a set
            model_extensions = set(row['extensions']) if isinstance(row['extensions'], (list, set)) else set()
            has_pickle = any(ext in model_extensions for ext in pickle_formats)
            has_safetensors = safetensors_format in model_extensions
            
            if has_pickle and not has_safetensors:
                pickle_only_models.append(row['model_id'])
                pickle_only_downloads.append(row['downloads'])  # Store the downloads
        
        # Save models and their downloads to a file
        with open('pickle_only_models_mar2025.txt', 'w') as f:
            for model, downloads in zip(pickle_only_models, pickle_only_downloads):
                f.write(f"{model}, {int(downloads)}\n")
            f.write(f"\nTotal models: {len(pickle_only_models)}")

        # Save safetensors-only models too
        safetensors_only_list = []
        safetensors_only_dl = []
        for _, row in mar25_data.iterrows():
            model_extensions = set(row['extensions']) if isinstance(row['extensions'], (list, set)) else set()
            has_pickle = any(ext in model_extensions for ext in pickle_formats)
            has_safetensors = safetensors_format in model_extensions
            
            if has_safetensors and not has_pickle:
                safetensors_only_list.append(row['model_id'])
                safetensors_only_dl.append(row['downloads'])
                
        with open('safetensors_only_models_mar2025.txt', 'w') as f:
            for model, downloads in zip(safetensors_only_list, safetensors_only_dl):
                f.write(f"{model}, {int(downloads)}\n")
            f.write(f"\nTotal models: {len(safetensors_only_list)}")

        # Print random sample of 20 models (for console output)
        print("Models from March 2025 with pickle format but no safetensors:")
        sample_size = min(20, len(pickle_only_models))
        indices = np.random.choice(len(pickle_only_models), size=sample_size, replace=False)
        for idx in indices:
            print(f"  - {pickle_only_models[idx]} ({pickle_only_downloads[idx]:,} downloads)")
        if len(pickle_only_models) > 20:
            print(f"  ... and {len(pickle_only_models) - 20} more")


    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(14, 8))
    ax2 = ax1.twinx()

    # Define colors
    pickle_color = '#2ecc71'  # green
    pickle_no_safe_color = '#e74c3c'  # red
    safetensors_only_color = '#3498db'  # blue

    # Plot number of models (solid lines)
    line1 = ax1.plot(dates, pickle_models, 
                     color=pickle_color, linewidth=2.5, marker='o',
                     label='Repos with Pickle Format')
    line2 = ax1.plot(dates, pickle_no_safe_models,
                     color=pickle_no_safe_color, linewidth=2.5, marker='o',
                     label='Repos with Pickle (No SafeTensors)')
    line3 = ax1.plot(dates, safetensors_only_models,
                     color=safetensors_only_color, linewidth=2.5, marker='o',
                     label='Repos with SafeTensors Only')

    # Plot downloads (dashed lines)
    line4 = ax2.plot(dates, pickle_downloads,
                     color=pickle_color, linewidth=2.5, marker='s', linestyle='--',
                     label='Downloads (Pickle Format)')
    line5 = ax2.plot(dates, pickle_no_safe_downloads,
                     color=pickle_no_safe_color, linewidth=2.5, marker='s', linestyle='--',
                     label='Downloads (Pickle, No SafeTensors)')
    line6 = ax2.plot(dates, safetensors_only_downloads,
                     color=safetensors_only_color, linewidth=2.5, marker='s', linestyle='--',
                     label='Downloads (SafeTensors Only)')

    if show_labels:
        # Keep original spacing settings for pickle and pickle_no_safe labels
        for i, (value1, value2, value3) in enumerate(zip(pickle_downloads, pickle_no_safe_downloads, safetensors_only_downloads)):
            # Calculate vertical spacing based on the values
            spacing = (max(value1, value2) - min(value1, value2)) / max(value1, value2)
            
            # Adjust vertical offsets based on proximity
            if spacing < 0.5:  # If values are within 50% of each other
                # Spread out the labels more vertically
                ax2.annotate(f'{value1/1e6:.1f}M',
                            (dates[i], value1),
                            xytext=(-5, 20),
                            textcoords='offset points',
                            ha='center', va='bottom',
                            fontsize=12, color=pickle_color)
                
                ax2.annotate(f'{value2/1e6:.1f}M',
                            (dates[i], value2),
                            xytext=(0, 10),
                            textcoords='offset points',
                            ha='center', va='top',
                            fontsize=12, color=pickle_no_safe_color)
                
                ax2.annotate(f'{value3/1e6:.1f}M',
                            (dates[i], value3),
                            xytext=(5, 25),
                            textcoords='offset points',
                            ha='center', va='top',
                            fontsize=12, color=safetensors_only_color)
            else:
                # Use standard positioning when values are sufficiently different
                ax2.annotate(f'{value1/1e6:.1f}M',
                            (dates[i], value1),
                            xytext=(0, 10),
                            textcoords='offset points',
                            ha='center', va='bottom',
                            fontsize=12, color=pickle_color)
                
                ax2.annotate(f'{value2/1e6:.1f}M',
                            (dates[i], value2),
                            xytext=(0, -12),
                            textcoords='offset points',
                            ha='center', va='top',
                            fontsize=12, color=pickle_no_safe_color)
            
                # Add safetensors-only label with a horizontal offset to avoid overlap
                ax2.annotate(f'{value3/1e6:.1f}M',
                            (dates[i], value3),
                            xytext=(-5, 10),
                            textcoords='offset points',
                            ha='left', va='center',
                            fontsize=12, color=safetensors_only_color)

    # Customize axes
    ax1.set_xlabel('Date', fontsize=20)
    ax1.set_ylabel('Number of Repositories', fontsize=20)
    ax2.set_ylabel('Monthly Downloads', fontsize=20)

    # Set y-axis to start at 0
    ax1.set_ylim(bottom=0)  # Ensure left y-axis starts at 0

    # Format y-axis with comma separator for thousands
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))

    # Customize ticks
    plt.xticks(rotation=45, fontsize=16)
    ax1.tick_params(axis='y', labelsize=16)
    ax2.tick_params(axis='y', labelsize=16)

    # Add grid
    ax1.grid(True, linestyle='--', alpha=0.4)

    # Combine legends from both axes
    lines = line1 + line2 + line3 + line4 + line5 + line6
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, fontsize=16, loc='upper left')

    # Save plot
    plt.tight_layout()
    plt.savefig(f'figure2.png', 
                dpi=300, bbox_inches='tight')
    plt.close()

def analyze_march_2025_data(data: pd.DataFrame):
    """Analyze March 2025 data for model and download percentages."""
    # Filter for August 2024 data
    mar_data = data[data['date'] == datetime(2025, 3, 17)]
    
    if mar_data.empty:
        logger.error("No data found for March 2025")
        return
    
    # Calculate total models and downloads
    total_models = len(mar_data)
    total_downloads = mar_data['downloads'].sum()
    
    # Define formats
    pickle_formats = {'pkl', 'pickle', 'joblib', 'dill', 'pt', 'pth', 'bin'}
    
    # Create masks for each category
    pickle_only_mask = mar_data['extensions'].apply(
        lambda exts: any(ext in pickle_formats for ext in exts) 
        and 'safetensors' not in exts
        and 'gguf' not in exts
    )
    
    safetensors_only_mask = mar_data['extensions'].apply(
        lambda exts: 'safetensors' in exts 
        and not any(ext in pickle_formats for ext in exts)
        and 'gguf' not in exts
    )
    
    both_pickle_safe_mask = mar_data['extensions'].apply(
        lambda exts: 'safetensors' in exts 
        and any(ext in pickle_formats for ext in exts)
        and 'gguf' not in exts
    )
    
    gguf_mask = mar_data['extensions'].apply(
        lambda exts: 'gguf' in exts
    )
    
    # Add new mask for all models with pickle (regardless of safetensors)
    has_pickle_mask = mar_data['extensions'].apply(
        lambda exts: any(ext in pickle_formats for ext in exts)
    )
    
    # Calculate counts and percentages for each category
    categories = {
        'Pickle only': {
            'models': sum(pickle_only_mask),
            'downloads': mar_data[pickle_only_mask]['downloads'].sum()
        },
        'SafeTensors only': {
            'models': sum(safetensors_only_mask),
            'downloads': mar_data[safetensors_only_mask]['downloads'].sum()
        },
        'Both Pickle & SafeTensors': {
            'models': sum(both_pickle_safe_mask),
            'downloads': mar_data[both_pickle_safe_mask]['downloads'].sum()
        },
        'GGUF': {
            'models': sum(gguf_mask),
            'downloads': mar_data[gguf_mask]['downloads'].sum()
        },
        'Has Pickle (Total)': {
            'models': sum(has_pickle_mask),
            'downloads': mar_data[has_pickle_mask]['downloads'].sum()
        }
    }
    
    # Calculate percentages and log results
    logger.info("\nMarch 2025 Analysis:")
    logger.info(f"Total models: {total_models:,}")
    logger.info(f"Total downloads: {total_downloads:,}")
    
    results = {}
    for category, stats in categories.items():
        model_percentage = (stats['models'] / total_models) * 100
        download_percentage = (stats['downloads'] / total_downloads) * 100
        
        logger.info(f"\n{category}:")
        logger.info(f"Models: {stats['models']:,} ({model_percentage:.1f}%)")
        logger.info(f"Downloads: {stats['downloads']:,} ({download_percentage:.1f}%)")
        
        results[category] = {
            'model_percentage': model_percentage,
            'download_percentage': download_percentage
        }
    
    return results

def main() -> None:
    # Configure logging and load data as needed
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    # Initialize dictionaries to store usage data
    extensions_usage = {}
    safetensors_usage = {}
    tags_usage = {}
    all_unknown_extensions = Counter()

    all_data = load_data()
    relevant_extensions = {
        'bin', 'h5', 'hdf5', 'ckpt', 'pkl', 'pickle', 'dill',
        'pth', 'pt', 'model', 'pb', 'joblib', 'npy', 'npz',
        'safetensors', 'onnx', 'msgpack', 'nemo', 'wav', 'gguf', 'keras', 'llamafile'
    }

    data_frames = []
    for df in all_data:
        if df.empty:
            continue

        # Attempt to retrieve the date for the current DataFrame
        if 'date' in df.columns and not df['date'].isna().all():
            date = df['date'].iloc[0]  # Use the first date in the column
        else:
            logger.warning("Date column missing or empty in DataFrame; assigning default date")
            date = datetime(1970, 1, 1)  # Assign a default date if missing

        # Extract filenames and model names
        filenames_series = df.get('filenames', pd.Series(['']*len(df)))
        model_names = df.get('model_id', pd.Series(['']*len(df)))

        # Call extraction function to handle relevant extensions
        extensions_series = extract_relevant_extensions(filenames_series, model_names, relevant_extensions)

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
            'date': date,
            'downloads': df['downloads'] if 'downloads' in df.columns else 0  # Add downloads column
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

    # Generate both versions of the plots
    plot_pickle_downloads(full_data, show_labels=True)

    # Add this after loading the data:
    march_stats = analyze_march_2025_data(full_data)

if __name__ == "__main__":
    main()
