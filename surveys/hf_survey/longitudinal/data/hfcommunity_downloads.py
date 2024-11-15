import requests
import zipfile_deflate64 as zipfile
import subprocess
import os
from pathlib import Path
import shlex
import mysql.connector
import csv

# List of Zenodo file URLs (you can extract these URLs manually or through Zenodo API)
zenodo_urls = [
    "https://zenodo.org/records/7743893/files/dump_241122.zip?download=1",
    "https://zenodo.org/records/7743896/files/dump_090323.zip?download=1",
    "https://zenodo.org/records/7855371/files/dump_180423.zip?download=1",
    "https://zenodo.org/records/7943753/files/dump_051523.zip?download=1",
    "https://zenodo.org/records/8112880/files/dump_20230630.zip?download=1",
    "https://zenodo.org/records/8112883/files/dump_072823.zip?download=1",
    "https://zenodo.org/records/8240989/files/dump_20230812.zip?download=1",
    "https://zenodo.org/records/8324809/files/dump_20230907.zip?download=1",
    "https://zenodo.org/records/10020642/files/dump_20231009.zip?download=1", 
    "https://zenodo.org/records/13929743/files/dump_hfc_20241001.zip?download=1"
]

# Local directory where files will be saved
path_data = Path("./")
extracted_path = path_data / "hfcommunity"

# Database credentials
db_user = "root"
db_password = "19980818"

# Function to download and save files
def download_file(url, save_path):
    local_filename = save_path / url.split('/')[-1]
    if local_filename.exists():
        print(f"File {local_filename} already exists. Skipping download.")
        return local_filename
    
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"File downloaded as {local_filename}")
        return local_filename
    else:
        print(f"Failed to download file from {url}")
        return None

# Function to extract a zip file
def extract_zip(file_path, extract_to):
    try:
        # Create a subfolder based on the zip file's name
        subfolder_name = file_path.stem
        subfolder_path = extract_to / subfolder_name
        
        if subfolder_path.exists() and any(subfolder_path.iterdir()):
            print(f"Folder {subfolder_path} already exists and is not empty. Skipping extraction.")
            return subfolder_path
        
        subfolder_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(file_path, 'r') as zf:
            zf.extractall(path=subfolder_path)
        print(f"Extracted {file_path} to {subfolder_path}")
        return subfolder_path
    except Exception as e:
        print(f"An error occurred while extracting {file_path}: {e}")
        return None

# Function to load a .sql file into the MariaDB database
def load_sql_to_mariadb(sql_file, db_name):
    try:
        print(f"Loading {sql_file} into the database {db_name}...")
        # Drop the database, ignore errors if it doesn't exist
        drop_command = f"mysql -u {db_user} -p{db_password} -e 'DROP DATABASE IF EXISTS {db_name}'"
        result = subprocess.run(drop_command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Warning: Could not drop database {db_name}: {result.stderr.strip()}")
        else:
            print(f"Database {db_name} dropped successfully.")
        
        # Create the database
        create_command = f"mysql -u {db_user} -p{db_password} -e 'CREATE DATABASE {db_name}'"
        subprocess.run(create_command, shell=True, check=True)
        print(f"Database {db_name} created successfully.")
        
        # Now load the SQL file
        command = f"mysql -u {db_user} -p{db_password} {db_name} < {sql_file}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to load {sql_file}: {result.stderr}")
        else:
            print(f"{sql_file} successfully loaded into the database {db_name}.")
    except Exception as e:
        print(f"An error occurred while loading {sql_file}: {e}")

# Function to export the models table to a CSV file
def export_model_with_tags_to_csv(db_name, output_file):
    try:
        print(f"Exporting 'model' table with tags and filenames from {db_name} to {output_file}...")
        
        conn = mysql.connector.connect(
            host="localhost",
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        
        # List all tables before executing the query
        list_tables(db_name)
        
        query = """
        SELECT 
            model.model_id, 
            model.downloads, 
            GROUP_CONCAT(DISTINCT model.library_name SEPARATOR ', ') AS library_names,
            GROUP_CONCAT(DISTINCT tag.name SEPARATOR ', ') AS tag_names,
            GROUP_CONCAT(DISTINCT file.filename SEPARATOR ', ') AS filenames
        FROM model
        LEFT JOIN repository ON model.model_id = repository.id
        LEFT JOIN tags_in_repo ON repository.id = tags_in_repo.repo_id
        LEFT JOIN tag ON tags_in_repo.tag_name = tag.name
        JOIN file ON model.model_id = file.repo_id
        GROUP BY model.model_id
        """

        cursor.execute(query)
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Get column names
        column_names = [i[0] for i in cursor.description]
        
        # Write to CSV file
        with open(output_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(column_names)  # Write header
            csvwriter.writerows(rows)  # Write data
        
        print(f"'model' table with tags successfully exported to {output_file}")
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except IOError as e:
        print(f"I/O error({e.errno}): {e.strerror}")
    except Exception as e:
        print(f"An error occurred while exporting 'model' table with tags: {e}")

# New function to list all tables in the database
def list_tables(db_name):
    try:
        print(f"Listing all tables in the database {db_name}...")
        conn = mysql.connector.connect(
            host="localhost",
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Tables in the database {db_name}:")
        for table in tables:
            print(table)
        cursor.close()
        conn.close()
        return tables
    except Exception as e:
        print(f"An error occurred while listing tables: {e}")
        return []

# Ensure the data directory exists
path_data.mkdir(parents=True, exist_ok=True)
extracted_path.mkdir(parents=True, exist_ok=True)

# Loop through all URLs, download, and extract files
extracted_folders = []
for url in zenodo_urls:
    # Extract the folder name from the URL
    folder_name = url.split('/')[-1].split('?')[0].replace('.zip', '')
    unique_extract_path = extracted_path / folder_name

    # Check if the extracted folder already exists
    if unique_extract_path.exists() and any(unique_extract_path.iterdir()):
        print(f"Folder {unique_extract_path} already exists and is not empty. Skipping download and extraction.")
        extracted_folders.append((unique_extract_path, folder_name))
    else:
        zip_file = download_file(url, path_data)
        if zip_file:
            extracted_folder = extract_zip(zip_file, extracted_path)
            if extracted_folder:
                extracted_folders.append((extracted_folder, folder_name))

# Find and load all .sql files into the MariaDB database
for folder, dump_name in extracted_folders:
    for sql_file in folder.glob("*.sql"):
        load_sql_to_mariadb(sql_file, dump_name)
    
    # Export the 'models' table to a CSV file for each dump
    output_csv = path_data / f"{dump_name}.csv"
    export_model_with_tags_to_csv(dump_name, output_csv)
