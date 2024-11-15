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
    df = df[df['downloads'] > 100]  # Filter models with over 100 downloads

    return df

def load_hfcommunity_data(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path, dtype={'tag_names': str, 'filenames': str, 'libraries': str, 'model_id': str})
    df = df[df['downloads'] > 100]  # Filter models with over 100 downloads

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
    df = df[df['downloads'] > 100]  # Filter models with over 100 downloads
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

    # Save categorized files
    categories = [
        'pickle_variant_with_safetensors',
        'pickle_variant_without_safetensors',
        'pytorch_variant_with_safetensors',
        'pytorch_variant_without_safetensors',
        'no_model_files'
    ]
    for category in categories:
        category_df = df[df['model_category'] == category]
        category_df.drop('siblings', axis=1).to_csv(f'top_models_{date.strftime("%d%b")}_{category}.csv', index=False)

    # Save models with security status
    if 'securitystatus' in df.columns:
        security_df = df[df['securitystatus'].notna()]
        security_df.drop('siblings', axis=1).to_csv(f'top_models_{date.strftime("%d%b")}_with_security.csv', index=False)

    # Save main file with new category column, excluding siblings
    df.drop('siblings', axis=1).to_csv(f'top_models_{date.strftime("%d%b")}.csv', index=False)

    return df

def load_data() -> list:
    data_Aug24 = load_data_socket("./data/data_Socket_Aug.csv", datetime(2024, 8, 1))
    # data_Nov = load_data_socket("./data/data_Socket_Nov.csv", datetime(2024, 11, 1))

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
    # all_data = [data_Aug24, data_Nov, data_ptmtorrent] + data_hfcommunity
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
    models_without_relevant_extensions = []  # Track models without relevant extensions

    for filenames, model_name in zip(filenames_series, model_names):
        if pd.isna(filenames):
            extensions_list.append(set())
            models_without_relevant_extensions.append(model_name)
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

        # If no relevant extensions found, record the model name
        if not has_relevant_extension:
            models_without_relevant_extensions.append(model_name)

    # Save model names without relevant extensions to a .txt file
    with open('models_without_relevant_extensions.txt', 'w') as f:
        for model_name in models_without_relevant_extensions:
            f.write(f"{model_name}\n")

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


def plot_extensions_usage(extensions_usage: dict):
    dates = sorted(extensions_usage.keys())
    known_extensions = [
        'bin', 'h5', 'hdf5', 'ckpt', 'pkl', 'pickle',
        'dill', 'pth', 'pt', 'model', 'pb', 'joblib',
        'npy', 'npz', 'safetensors', 'onnx', 'msgpack',
        'nemo', 'wav', 'gguf', 'keras', 'llamafile'
    ]
    extension_counts = {ext: [] for ext in known_extensions}

    # Get the most recent date's statistics
    latest_date = dates[-1]
    latest_usage = extensions_usage[latest_date]
    total_models = sum(latest_usage.values())

    # Calculate grouped statistics
    pytorch_formats = sum(latest_usage.get(ext, 0) for ext in ['pt', 'pth', 'bin'])
    pickle_formats = sum(latest_usage.get(ext, 0) for ext in ['pkl', 'pickle', 'joblib', 'dill'])
    model_format = latest_usage.get('model', 0)

    # Rest of the plotting code remains the same...
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

def plot_pickle_safetensors_proportion(data: pd.DataFrame):
    # Redefine formats
    pickle_formats = {'pkl', 'pickle', 'joblib', 'dill', 'pt', 'pth', 'bin'}
    safetensors_format = 'safetensors'
    gguf_format = 'gguf'  # New format to track separately

    # Initialize lists for storing proportions over time
    pickle_with_safetensors = []    # Has pickle-based format AND safetensors
    pickle_without_safetensors = [] # Has pickle-based format but NO safetensors
    safetensors_without_pickle = [] # Has safetensors but NO pickle formats
    gguf_models = []               # Has GGUF format
    other_or_missing = []          # Other formats or missing

    total_counts = []  # For sample size annotations
    proportion_data = []  # For saving proportions to a txt file

    # Analyze data by date
    dates = sorted(data['date'].unique())
    for date in dates:
        subset = data[data['date'] == date]
        total_count = len(subset)
        total_counts.append(total_count)
        
        # Counters for each category
        count_pickle_with_st = 0
        count_pickle_without_st = 0
        count_safetensors_without_pickle = 0
        count_gguf = 0             # New counter for GGUF
        count_other_or_missing = 0

        for extensions in subset['extensions']:
            has_pickle_format = any(ext in pickle_formats for ext in extensions)
            has_safetensors = safetensors_format in extensions
            has_gguf = gguf_format in extensions  # Check for GGUF

            if has_gguf:
                count_gguf += 1    # Prioritize GGUF classification
            elif not extensions:    # Empty set
                count_other_or_missing += 1
            elif has_pickle_format:
                if has_safetensors:
                    count_pickle_with_st += 1
                else:
                    count_pickle_without_st += 1
            elif has_safetensors:
                count_safetensors_without_pickle += 1
            else:
                count_other_or_missing += 1

        # Calculate proportions including GGUF
        pickle_with_safetensors.append(count_pickle_with_st / total_count)
        pickle_without_safetensors.append(count_pickle_without_st / total_count)
        safetensors_without_pickle.append(count_safetensors_without_pickle / total_count)
        gguf_models.append(count_gguf / total_count)
        other_or_missing.append(count_other_or_missing / total_count)

        # Update proportion data to include GGUF
        proportion_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'total_models': total_count,
            'pickle_with_safetensors': count_pickle_with_st / total_count,
            'pickle_without_safetensors': count_pickle_without_st / total_count,
            'safetensors_without_pickle': count_safetensors_without_pickle / total_count,
            'gguf_models': count_gguf / total_count,
            'other_or_missing': count_other_or_missing / total_count
        })

    # Calculate top 100 statistics for each date
    top100_stats = []
    for date in dates:
        subset = data[data['date'] == date]
        # Sort by downloads if available, otherwise use all models
        if 'downloads' in subset.columns:
            top100 = subset.nlargest(100, 'downloads')
        else:
            top100 = subset.head(100)
        
        total_top100 = len(top100)
        if total_top100 == 0:
            continue
            
        # Count formats in top 100
        pickle_no_st = sum(1 for exts in top100['extensions'] if 
                          any(ext in pickle_formats for ext in exts) and 
                          safetensors_format not in exts)
        pickle_with_st = sum(1 for exts in top100['extensions'] if 
                            any(ext in pickle_formats for ext in exts) and 
                            safetensors_format in exts)
        st_no_pickle = sum(1 for exts in top100['extensions'] if 
                          safetensors_format in exts and 
                          not any(ext in pickle_formats for ext in exts))
        gguf = sum(1 for exts in top100['extensions'] if 
                   gguf_format in exts)
        other = total_top100 - pickle_no_st - pickle_with_st - st_no_pickle - gguf
        
        top100_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'pickle_no_st': pickle_no_st,
            'pickle_with_st': pickle_with_st,
            'st_no_pickle': st_no_pickle,
            'gguf': gguf,
            'other': other
        })

    # Save top-100 statistics to a file
    with open('top100_format_stats.txt', 'w') as f:
        f.write('Date\tPickle w/o ST\tPickle w/ ST\tST w/o Pickle\tGGUF\tOther\n')
        for stat in top100_stats:
            f.write(f"{stat['date']}\t{stat['pickle_no_st']}\t{stat['pickle_with_st']}\t"
                   f"{stat['st_no_pickle']}\t{stat['gguf']}\t{stat['other']}\n")

    # Log the most recent top-100 statistics
    if top100_stats:
        latest = top100_stats[-1]
        logger.info(f"\nLatest Top-100 Models Format Distribution (as of {latest['date']}):")
        logger.info(f"Pickle without SafeTensors: {latest['pickle_no_st']}")
        logger.info(f"Pickle with SafeTensors: {latest['pickle_with_st']}")
        logger.info(f"SafeTensors without Pickle: {latest['st_no_pickle']}")
        logger.info(f"GGUF: {latest['gguf']}")
        logger.info(f"Other: {latest['other']}")

    # Update file writing to include GGUF
    with open('proportions_over_time.txt', 'w') as f:
        f.write('Date\tTotal Models\tHas Pickle w/ SafeTensors\tHas Pickle w/o SafeTensors\tHas SafeTensors w/o Pickle\tHas GGUF\tOther Format or Missing\n')
        for entry in proportion_data:
            f.write(f"{entry['date']}\t{entry['total_models']}\t{entry['pickle_with_safetensors']:.4f}\t"
                   f"{entry['pickle_without_safetensors']:.4f}\t{entry['safetensors_without_pickle']:.4f}\t"
                   f"{entry['gguf_models']:.4f}\t{entry['other_or_missing']:.4f}\n")

    # Convert dates to datetime objects for plotting
    dates_dt = pd.to_datetime(dates)

    # Determine the x-axis range
    min_date = dates_dt.min()
    max_date = dates_dt.max()
    date_range = max_date - min_date

    # Extend the x-axis to the left by 5% of the date range to accommodate out-of-range events
    extended_min_date = min_date - pd.Timedelta(days=0.05 * date_range.days)

    plt.figure(figsize=(14, 8))  # Increased figure size
    plt.rcParams.update({'font.size': 16})  # Adjust base font size

    # Define colors for better visibility
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#f1c40f', '#9b59b6']  # Added color for GGUF

    # Prepare data for plotting
    proportions = [
        (pickle_without_safetensors, 'Has Pickle w/o SafeTensors'),
        (pickle_with_safetensors, 'Has Pickle w/ SafeTensors'),
        (safetensors_without_pickle, 'Has SafeTensors w/o Pickle'),
        (gguf_models, 'GGUF only'),
        (other_or_missing, 'Other format or missing')
    ]

    # Plot each line
    last_points = []
    for (y_data, label), color in zip(proportions, colors):
        fontweight = 'bold'
        plt.plot(dates_dt, [y * 100 for y in y_data], marker='o', label=label, linewidth=2.5,
                 markersize=8, color=color)
        last_points.append((y_data[-1] * 100, label, color))

    # Sort the last points by y-value
    last_points.sort(reverse=True)  # Highest y at the top

    # Define y-offsets to prevent overlaps
    y_offsets = [0, 10, -5, -5, -5]  # Adjust as needed based on number of lines

    # Annotate the last points with adjusted positions to avoid overlaps
    for (y, label, color), y_offset in zip(last_points, y_offsets):
        x = dates_dt[-1]  # Changed from dates_dt.iloc[-1] to dates_dt[-1]
        plt.annotate(f'{y:.1f}%', 
                     (x, y),
                     textcoords="offset points", 
                     xytext=(10, y_offset),
                     ha='left',
                     va='center',
                     fontsize=20,
                     fontweight='bold',
                     color=color,
                     bbox=dict(facecolor='white', 
                               edgecolor='none',
                               alpha=0.7))

    # Add total counts at the top of the plot with vertical text
    y_max = plt.gca().get_ylim()[1]
    for i, (date, total) in enumerate(zip(dates_dt, total_counts)):
        
        plt.annotate(f'N={total}', 
                     (date, y_max),
                     textcoords="offset points", 
                     xytext=(-5, 55),  # Modified y-offset
                     ha='center',
                     va='top',
                     fontsize=18,
                     rotation=90
                     )  # Rotate text vertically

    # Add vertical lines for important dates
    events = [
        ('2022-09-01', 'SafeTensors Released (2022-09)'),
        ('2023-03-15', 'SafeTensors Convert Bot'),
    ]

    for event_date_str, event_label in events:
        event_date = pd.to_datetime(event_date_str)
        
        if min_date <= event_date <= max_date:
            # Draw a vertical line for each event date within the range
            plt.axvline(x=event_date, color='blue', linestyle='--', linewidth=2, alpha=0.7)
            
            # Annotate the event with rotated vertical text at the top
            plt.annotate(event_label, 
                         (event_date, y_max),  # Set y position to top of y-axis
                         textcoords="offset points", 
                         xytext=(15, 50),  # Position text close to the top
                         ha='center', 
                         va='top', 
                         rotation=90,  # Rotate text vertically
                         fontsize=20, 
                         color='blue', 
                         bbox=dict(facecolor='white', edgecolor='none', alpha=0.6))
        elif event_date < min_date:
            # For events before the data range, place the vertical line and annotation at the extended minimum date
            plt.axvline(x=extended_min_date, color='blue', linestyle='--', linewidth=2, alpha=0.7)
            # Annotate at extended_min_date
            plt.annotate(event_label, 
                         (extended_min_date, y_max),
                         textcoords="offset points", 
                         xytext=(15, 50),
                         ha='center',
                         va='top',
                         rotation=90,
                         fontsize=20,
                         color='blue',
                         bbox=dict(facecolor='white', edgecolor='none', alpha=0.6))
        else:
            # For events after the data range, place the vertical line at max_date
            plt.axvline(x=max_date, color='blue', linestyle='--', linewidth=2, alpha=0.7)
            # Annotate at max_date
            plt.annotate(event_label, 
                         (max_date, y_max+20),
                         textcoords="offset points", 
                         xytext=(15, 50),
                         ha='center',
                         va='top',
                         rotation=90,
                         fontsize=20,
                         color='blue',
                         bbox=dict(facecolor='white', edgecolor='none', alpha=0.6))

    # Customize legend and grid for readability
    plt.legend(fontsize=18, loc='upper right', bbox_to_anchor=(0.93, 1))
    plt.grid(True, linestyle='--', alpha=0.4)

    # Set axis titles and percentage format for y-axis
    plt.xlabel('Date', fontsize=20)
    plt.ylabel('Percentage (%)', fontsize=20)
    plt.ylim(0, 115)  # Increased from 105 to 110 to better accommodate labels

    # Adjust x-axis limits to include the extended minimum date
    plt.xlim(extended_min_date, max_date)

    # Increase tick label sizes and rotate x-axis labels
    plt.xticks(fontsize=20, rotation=45)
    plt.yticks(fontsize=20)

    # Save detailed statistics to a file
    with open('format_statistics.txt', 'w') as f:
        f.write("Format Distribution Statistics Over Time\n")
        f.write("======================================\n\n")
        
        for date, total in zip(dates_dt, total_counts):
            date_str = date.strftime('%Y-%m-%d')
            f.write(f"\nDate: {date_str}\n")
            f.write(f"Total Models: {total}\n")
            f.write("-" * 40 + "\n")
            
            # Get index for this date
            idx = dates_dt.get_loc(date)
            
            # Calculate raw counts for each category
            pickle_no_st_count = int(pickle_without_safetensors[idx] * total)
            pickle_with_st_count = int(pickle_with_safetensors[idx] * total)
            st_no_pickle_count = int(safetensors_without_pickle[idx] * total)
            gguf_count = int(gguf_models[idx] * total)
            other_count = int(other_or_missing[idx] * total)
            
            # Write counts and percentages
            categories = [
                ("Pickle without SafeTensors", pickle_no_st_count, pickle_without_safetensors[idx] * 100),
                ("Pickle with SafeTensors", pickle_with_st_count, pickle_with_safetensors[idx] * 100),
                ("SafeTensors without Pickle", st_no_pickle_count, safetensors_without_pickle[idx] * 100),
                ("GGUF only", gguf_count, gguf_models[idx] * 100),
                ("Other format or missing", other_count, other_or_missing[idx] * 100)
            ]
            
            for category, count, percentage in categories:
                f.write(f"{category}: {count:,} ({percentage:.1f}%)\n")
            
            # Calculate and write totals with SafeTensors
            total_with_st = pickle_with_st_count + st_no_pickle_count
            total_with_st_pct = (pickle_with_safetensors[idx] + safetensors_without_pickle[idx]) * 100
            f.write(f"\nTotal models with SafeTensors: {total_with_st:,} ({total_with_st_pct:.1f}%)\n")

    # Use tight layout to prevent label cutoff and save the figure
    plt.tight_layout()
    plt.savefig('pickle_safetensors_proportion.png', dpi=300, bbox_inches='tight')
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

def compute_extension_proportions(data: pd.DataFrame, known_extensions: list):
    # Initialize lists to store results
    proportion_results = []
    count_results = []
    dates = sorted(data['date'].unique())
    
    for date in dates:
        subset = data[data['date'] == date]
        total_models = len(subset)
        
        # Initialize a dictionary to store counts for this date
        extension_counts = {ext: 0 for ext in known_extensions}
        
        for extensions in subset['extensions']:
            exts = set(extensions)
            for ext in exts:
                if ext in known_extensions:
                    extension_counts[ext] += 1
        
        # Compute proportions
        extension_proportions = {ext: (count / total_models if total_models else 0) 
                               for ext, count in extension_counts.items()}
        
        # Store the results
        base_entry = {'date': date.strftime('%Y-%m-%d'), 'total_models': total_models}
        
        # Store proportions
        proportion_entry = base_entry.copy()
        proportion_entry.update(extension_proportions)
        proportion_results.append(proportion_entry)
        
        # Store raw counts
        count_entry = base_entry.copy()
        count_entry.update(extension_counts)
        count_results.append(count_entry)
    
    # Save both to CSV files
    pd.DataFrame(proportion_results).to_csv('extension_proportions_over_time.csv', index=False)
    pd.DataFrame(count_results).to_csv('extension_counts_over_time.csv', index=False)

def plot_pickle_safetensors_counts(data: pd.DataFrame):
    # Redefine formats (same as in proportion plot)
    pickle_formats = {'pkl', 'pickle', 'joblib', 'dill', 'pt', 'pth', 'bin'}
    safetensors_format = 'safetensors'
    gguf_format = 'gguf'

    # Initialize lists for storing absolute counts over time
    pickle_with_safetensors = []    
    pickle_without_safetensors = [] 
    safetensors_without_pickle = [] 
    gguf_models = []               
    other_or_missing = []          

    # Analyze data by date
    dates = sorted(data['date'].unique())
    for date in dates:
        subset = data[data['date'] == date]
        
        # Initialize counters
        count_pickle_with_st = 0
        count_pickle_without_st = 0
        count_safetensors_without_pickle = 0
        count_gguf = 0
        count_other_or_missing = 0

        for extensions in subset['extensions']:
            has_pickle_format = any(ext in pickle_formats for ext in extensions)
            has_safetensors = safetensors_format in extensions
            has_gguf = gguf_format in extensions

            if has_gguf:
                count_gguf += 1
            elif not extensions:
                count_other_or_missing += 1
            elif has_pickle_format:
                if has_safetensors:
                    count_pickle_with_st += 1
                else:
                    count_pickle_without_st += 1
            elif has_safetensors:
                count_safetensors_without_pickle += 1
            else:
                count_other_or_missing += 1

        # Store absolute counts
        pickle_with_safetensors.append(count_pickle_with_st)
        pickle_without_safetensors.append(count_pickle_without_st)
        safetensors_without_pickle.append(count_safetensors_without_pickle)
        gguf_models.append(count_gguf)
        other_or_missing.append(count_other_or_missing)

    # Convert dates to datetime objects for plotting
    dates_dt = pd.to_datetime(dates)

    # Create the figure
    plt.figure(figsize=(14, 8))
    plt.rcParams.update({'font.size': 16})

    # Define colors (same as proportion plot for consistency)
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#f1c40f', '#9b59b6']

    # Prepare data for plotting
    counts_data = [
        (pickle_without_safetensors, 'Has Pickle w/o SafeTensors'),
        (pickle_with_safetensors, 'Has Pickle w/ SafeTensors'),
        (safetensors_without_pickle, 'Has SafeTensors w/o Pickle'),
        (gguf_models, 'GGUF only'),
        (other_or_missing, 'Other format or missing')
    ]

    # Plot each line
    last_points = []
    for (y_data, label), color in zip(counts_data, colors):
        plt.plot(dates_dt, y_data, marker='o', label=label, linewidth=2.5,
                markersize=8, color=color)
        last_points.append((y_data[-1], label, color))

    # Sort the last points by y-value
    last_points.sort(reverse=True)

    # Define y-offsets to prevent overlaps
    y_offsets = [0, 10, -5, -5, -10]

    # Annotate the last points
    for (y, label, color), y_offset in zip(last_points, y_offsets):
        x = dates_dt[-1]
        plt.annotate(f'{int(y):,}', 
                    (x, y),
                    textcoords="offset points", 
                    xytext=(10, y_offset),
                    ha='left',
                    va='center',
                    fontsize=20,
                    fontweight='bold',
                    color=color,
                    bbox=dict(facecolor='white', 
                            edgecolor='none',
                            alpha=0.7))

    # Add vertical lines for important dates (same as proportion plot)
    events = [
        ('2022-09-01', 'SafeTensors Released (2022-09)'),
        ('2023-03-15', 'SafeTensors Convert Bot'),
    ]

    y_max = plt.gca().get_ylim()[1]
    for event_date_str, event_label in events:
        event_date = pd.to_datetime(event_date_str)
        if min(dates_dt) <= event_date <= max(dates_dt):
            plt.axvline(x=event_date, color='blue', linestyle='--', linewidth=2, alpha=0.7)
            plt.annotate(event_label, 
                        (event_date, y_max),
                        textcoords="offset points", 
                        xytext=(15, 10),
                        ha='center',
                        va='top',
                        rotation=90,
                        fontsize=20,
                        color='blue',
                        bbox=dict(facecolor='white', edgecolor='none', alpha=0.6))

    # Customize plot
    plt.legend(fontsize=18, loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.xlabel('Date', fontsize=20)
    plt.ylabel('Number of Models', fontsize=20)
    
    # Format y-axis with comma separator for thousands
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

    # Increase tick label sizes and rotate x-axis labels
    plt.xticks(fontsize=20, rotation=45)
    plt.yticks(fontsize=20)

    # Save the figure
    plt.tight_layout()
    plt.savefig('pickle_safetensors_counts.png', dpi=300, bbox_inches='tight')
    plt.close()

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

    # Plot Pickle-based formats proportion
    plot_pickle_safetensors_proportion(full_data)

    # Plot absolute counts
    plot_pickle_safetensors_counts(full_data)

    # Log full list of unknown extensions across all data
    logger.info(f"All unknown extensions across datasets: {all_unknown_extensions}")

    # Compute and save extension proportions
    compute_extension_proportions(full_data, relevant_extensions)

if __name__ == "__main__":
    main()
