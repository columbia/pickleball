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

def load_ptmtorrent_data(data_path: str) -> pd.DataFrame:
    with open(data_path, 'r') as file:
        data = json.load(file)

    # Create a list of dictionaries with model_id, tags, and downloads
    filtered_data = [
        {
            "model_id": item["id"],
            "tags": item["tags"],
            "downloads": item.get('downloads', 0)
        }
        for item in data
    ]

    # Convert the filtered data into a pandas DataFrame
    df = pd.DataFrame(filtered_data)
    
    # Sort by downloads in descending order and take the top 100,000
    df = df.sort_values('downloads', ascending=False).head(100000)
    
    return df


def load_hfcommunity_data(data_path: str) -> pd.DataFrame:
    conn = sqlite3.connect(data_path)
    cursor = conn.cursor()

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    logger.debug("Tables in the database:")
    for table in tables:
        logger.debug(f"- {table[0]}")
    
    # Get schema for the 'model' table
    cursor.execute("PRAGMA table_info(model)")
    schema = cursor.fetchall()
    
    logger.debug("Schema of the 'model' table:")
    for column in schema:
        logger.debug(f"- {column[1]} ({column[2]})")
    exit(-1)
    # Updated query to get more relevant information
    query = """
        SELECT m.id AS model_id, m.downloads, m.likes, m.task_id, t.name AS task_name,
               GROUP_CONCAT(DISTINCT l.name) AS libraries
        FROM model m
        LEFT JOIN model_library ml ON m.id = ml.model_id
        LEFT JOIN library l ON ml.library_id = l.id
        LEFT JOIN task t ON m.task_id = t.id
        GROUP BY m.id
        ORDER BY m.downloads DESC
        LIMIT 1000
    """ 
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    logger.debug(f"Loaded {len(df)} rows from HFCommunity database")
    logger.debug(df.head(20))
    logger.debug(df.columns)
    return df


def load_data() -> pd.DataFrame:
    # data_Aug24 = pd.read_csv("./data/PeaTMOSS_Aug2024.csv")
    # data_peatmoss = load_peatmoss_data("./data/PeaTMOSS.db")
    # data_ptmtorrent = load_ptmtorrent_data("./data/PTMTorrent.json")
    data_hfcommunity = load_hfcommunity_data("./data/hfcommunity_241122.sql")
    exit(-1)
    # Combine the datasets
    return data_Aug24, data_peatmoss, data_ptmtorrent, data_hfcommunity


def analysis(data: pd.DataFrame) -> None:
    """
    Analyze the library usage of the models in each dataset
    """
    library_counter = Counter()
    total_rows = len(data)

    for _, row in data.iterrows():
        libraries = row["libraries"]
        if isinstance(libraries, str):
            libraries = eval(libraries)  # Convert string representation to list
        library_counter.update(libraries)

    print("Top 10 Library usage percentages:")
    for library, count in library_counter.most_common(10):
        percentage = (count / total_rows) * 100
        print(f"{library}: {percentage:.2f}%")


def main() -> None:
    data = load_data()
    analysis(data)

if __name__ == "__main__":
    main()
