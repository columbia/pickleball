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
import json
import pickle
import sqlite3
import pandas as pd
from collections import Counter
from loguru import logger
import matplotlib.pyplot as plt
from datetime import datetime

def load_ptmtorrent_data(data_path: str) -> pd.DataFrame:
    with open(data_path, 'r') as file:
        data = json.load(file)

    filtered_data = [
        {
            "model_id": item["id"],
            "tag_names": item["tag_names"],
            "downloads": item.get('downloads', 0)
        }
        for item in data
    ]

    df = pd.DataFrame(filtered_data)
    df = df.sort_values('downloads', ascending=False).head(100000)
    
    # Set the date to January 2023 for PTMTorrent data
    df['date'] = datetime(2023, 1, 1)
    
    return df


def load_hfcommunity_data(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    df = df.sort_values('downloads', ascending=False).head(100000)
    
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


def load_data() -> tuple:
    data_Aug24 = pd.read_csv("./data/PeaTMOSS_Aug2024.csv")
    data_Aug24['date'] = datetime(2024, 8, 1)
    
    data_ptmtorrent = load_ptmtorrent_data("./data/PTMTorrent.json")
    
    data_files = [f for f in os.listdir('./data') if f.startswith('dump_') and f.endswith('.csv')]
    data_hfcommunity = []
    
    for file in data_files:
        data = load_hfcommunity_data(f"./data/{file}")
        data_hfcommunity.append(data)
    
    return data_Aug24, data_ptmtorrent, data_hfcommunity


def extract_framework(tags):
    known_frameworks = ['pytorch', 'tf', 'jax', 'safetensors']
    
    if pd.isna(tags):
        return ['unknown']
    
    if isinstance(tags, str):
        tag_list = tags.split(', ')
    else:
        logger.warning(f"Unexpected tag type: {type(tags)}. Value: {tags}")
        return ['unknown']
    
    frameworks = [tag for tag in tag_list if tag in known_frameworks]
    
    # Add 'others' if there are tags not in known_frameworks
    if set(tag_list) - set(known_frameworks):
        frameworks.append('others')
    
    return frameworks if frameworks else ['unknown']


def analysis(data: pd.DataFrame) -> dict:
    framework_usage = {}
    
    for _, row in data.iterrows():
        date = row['date']
        tags = row.get('tag_names', row.get('tag_name'))
        frameworks = extract_framework(tags)
        
        if date not in framework_usage:
            framework_usage[date] = Counter()
        
        framework_usage[date].update(frameworks)
    
    return framework_usage


def plot_safetensor_usage(framework_usage: dict):
    dates = sorted(framework_usage.keys())
    safetensor_proportions = []
    
    for date in dates:
        date_usage = framework_usage[date]
        total = sum(sum(fw.values()) for fw in date_usage.values())
        safetensor_count = sum(fw.get('safetensors', 0) for fw in date_usage.values())
        proportion = safetensor_count / total if total > 0 else 0
        safetensor_proportions.append(proportion)
    
    plt.figure(figsize=(12, 6))
    plt.plot(dates, safetensor_proportions, marker='o')
    plt.title('Proportion of SafeTensor Usage Over Time')
    plt.xlabel('Date')
    plt.ylabel('Proportion of SafeTensor Usage')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('safetensor_usage.png')
    plt.close()


def main() -> None:
    data_files = [f for f in os.listdir('./data') if f.startswith('dump_') and f.endswith('.csv')]
    all_data = []
    
    for file in data_files:
        data = load_hfcommunity_data(f"./data/{file}")
        all_data.append(data)
        print(f"Columns in {file}: {data.columns.tolist()}")
    
    framework_usage = {}
    for df in all_data:
        date = df['date'].iloc[0]  # Assuming all rows in a DataFrame have the same date
        framework_usage[date] = analysis(df)
    
    print("Dates in the analysis:", list(framework_usage.keys()))
    plot_safetensor_usage(framework_usage)


if __name__ == "__main__":
    main()
