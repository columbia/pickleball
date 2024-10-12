import requests
import pyzipper
import subprocess
import os
from pathlib import Path

# List of Zenodo file URLs (you can extract these URLs manually or through Zenodo API)
zenodo_urls = [
    "https://zenodo.org/record/XXXXX/files/dump_file_1.zip",
    "https://zenodo.org/record/XXXXX/files/dump_file_2.zip",
    # Add all other URLs here
]

# Local directory where files will be saved
path_data = Path("/path/to/your/directory")
extracted_path = path_data / "extracted_files"

# Database credentials
db_name = "hfcommunity"
db_user = "root"
db_password = "your_password"  # Replace with your actual password

# Function to download and save files
def download_file(url, save_path):
    local_filename = save_path / url.split('/')[-1]
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
        with pyzipper.AESZipFile(file_path, 'r') as zf:
            zf.extractall(path=extract_to)
            print(f"Extracted {file_path} to {extract_to}")
    except Exception as e:
        print(f"An error occurred while extracting {file_path}: {e}")

# Function to load a .sql file into the MariaDB database
def load_sql_to_mariadb(sql_file):
    try:
        print(f"Loading {sql_file} into the database...")
        command = f"mysql -u {db_user} -p{db_password} {db_name} < {sql_file}"
        subprocess.run(command, shell=True, check=True)
        print(f"{sql_file} successfully loaded into the database.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to load {sql_file}: {e}")

# Function to export the models table to a CSV file
def export_table_to_csv(output_file):
    try:
        print(f"Exporting 'models' table to {output_file}...")
        query = f"SELECT * INTO OUTFILE '{output_file}' FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\n' FROM models;"
        command = f"mysql -u {db_user} -p{db_password} -e \"{query}\" {db_name}"
        subprocess.run(command, shell=True, check=True)
        print(f"'models' table successfully exported to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to export 'models' table: {e}")

# Ensure the data directory exists
path_data.mkdir(parents=True, exist_ok=True)
extracted_path.mkdir(parents=True, exist_ok=True)

# Loop through all URLs, download, and extract files
for url in zenodo_urls:
    zip_file = download_file(url, path_data)
    if zip_file:
        extract_zip(zip_file, extracted_path)

# Find and load all .sql files into the MariaDB database
for sql_file in extracted_path.glob("*.sql"):
    load_sql_to_mariadb(sql_file)

# Export the 'models' table to a CSV file
output_csv = path_data / "models_table.csv"
export_table_to_csv(output_csv)
