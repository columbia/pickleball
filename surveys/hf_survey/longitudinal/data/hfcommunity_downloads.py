import requests
import zipfile_deflate64 as zipfile
import subprocess
import os
from pathlib import Path
import shlex
import mysql.connector

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
]

# Local directory where files will be saved
path_data = Path("./")
extracted_path = path_data / "hfcommunity"

# Database credentials
db_name = "hfcommunity"
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
    # Create a unique folder name based on the zip file name
    folder_name = file_path.stem
    unique_extract_path = extract_to / folder_name
    
    if unique_extract_path.exists() and any(unique_extract_path.iterdir()):
        print(f"Folder {unique_extract_path} already exists and is not empty. Skipping extraction.")
        return unique_extract_path
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            zf.extractall(path=unique_extract_path)
            print(f"Extracted {file_path} to {unique_extract_path}")
        return unique_extract_path
    except zipfile.BadZipFile:
        print(f"Error: {file_path} is not a valid zip file.")
    except Exception as e:
        print(f"An error occurred while extracting {file_path}: {e}")
    return None

# Function to load a .sql file into the MariaDB database
def load_sql_to_mariadb(sql_file):
    try:
        print(f"Loading {sql_file} into the database...")
        command = f"mysql -u {db_user} -p{db_password} {db_name} < {sql_file}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to load {sql_file}: {result.stderr}")
        else:
            print(f"{sql_file} successfully loaded into the database.")
    except Exception as e:
        print(f"An error occurred while loading {sql_file}: {e}")

# Function to export the models table to a CSV file
def export_table_to_csv(output_file):
    try:
        # Use an absolute path
        abs_output_file = os.path.abspath(output_file)
        print(f"Attempting to export 'model' table to {abs_output_file}...")
        
        # Check if the directory exists and is writable
        output_dir = os.path.dirname(abs_output_file)
        if not os.path.exists(output_dir):
            print(f"Output directory {output_dir} does not exist. Attempting to create it.")
            os.makedirs(output_dir, exist_ok=True)
        
        if not os.access(output_dir, os.W_OK):
            print(f"Warning: The script does not have write permissions for {output_dir}")
        
        # Use the absolute path in the query
        query = f"SELECT * FROM model INTO OUTFILE '{abs_output_file}' FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\\n';"
        command = f"mysql -u {db_user} -p{db_password} -e {shlex.quote(query)} {db_name}"
        
        print(f"Executing command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to export 'model' table. Error: {result.stderr}")
            print(f"Command output: {result.stdout}")
        else:
            print(f"'model' table successfully exported to {abs_output_file}")
            
        # Check if the file was actually created
        if os.path.exists(abs_output_file):
            print(f"Confirmed: File {abs_output_file} exists.")
        else:
            print(f"Warning: File {abs_output_file} was not created.")
    
    except Exception as e:
        print(f"An error occurred while exporting 'model' table: {str(e)}")

# New function to list all tables in the database
def list_tables():
    try:
        print("Listing all tables in the database...")
        conn = mysql.connector.connect(
            host="localhost",
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Tables in the database:")
        for table in tables:
            print(table[0])
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred while listing tables: {e}")

# Ensure the data directory exists
path_data.mkdir(parents=True, exist_ok=True)
extracted_path.mkdir(parents=True, exist_ok=True)

# Create a 'data' folder for CSV files
data_folder = Path("./data")
data_folder.mkdir(parents=True, exist_ok=True)

# Loop through all URLs, download, and extract files
extracted_folders = []
for url in zenodo_urls:
    zip_file_name = url.split('/')[-1]
    folder_name = zip_file_name.split('.')[0]  # Remove the .zip extension
    unique_extract_path = extracted_path / folder_name

    if unique_extract_path.exists() and any(unique_extract_path.iterdir()):
        print(f"Extracted folder {unique_extract_path} already exists. Skipping download and extraction.")
        extracted_folders.append(unique_extract_path)
    else:
        zip_file = download_file(url, path_data)
        if zip_file:
            extracted_folder = extract_zip(zip_file, extracted_path)
            if extracted_folder:
                extracted_folders.append(extracted_folder)

# Find and load all .sql files into the MariaDB database
for folder in extracted_folders:
    for sql_file in folder.glob("*.sql"):
        load_sql_to_mariadb(sql_file)
    
    # List all tables after loading each SQL file
    # list_tables()
    
    # Export the 'models' table to a CSV file for each dump
    dump_name = folder.name
    output_csv = data_folder / f"models_table_{dump_name}.csv"
    export_table_to_csv(output_csv)
