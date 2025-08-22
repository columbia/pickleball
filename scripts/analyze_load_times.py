import pandas as pd
import os
import sys

file_path = os.path.dirname(os.path.realpath(__file__))
project_path = os.path.join(file_path, "..")
results_path = os.path.join(project_path, "results/times.csv")


# Read the CSV data into a pandas DataFrame
try:
    df = pd.read_csv(results_path, header=None, names=[
                     'library', 'version', 'time'])
except FileNotFoundError:
    print("Error: Load time results not found")
    sys.exit()

# Pivot the table to have 'vanilla' and 'pickleball' as columns for easy comparison
pivot_df = df.pivot(index='library', columns='version',
                    values='time').reset_index()
pivot_df.columns.name = None

# Ensure both 'vanilla' and 'pickleball' columns exist to avoid errors
if 'vanilla' in pivot_df.columns and 'pickleball' in pivot_df.columns:
    # Calculate the overhead as a percentage
    pivot_df['overhead_%'] = (
        (pivot_df['pickleball'] - pivot_df['vanilla']) / pivot_df['vanilla']) * 100

    header = f"{'Library':<15} | {'vanilla':<12} | {
        'pickleball':<12} | {'overhead'}"
    print(header)
    print("=" * len(header))

    # Iterate through the data and print each row in the table format
    for index, row in pivot_df.iterrows():
        library = row['library']
        vanilla_time = f"{row['vanilla']:.4f}s"
        pickleball_time = f"{row['pickleball']:.4f}s"
        # Use + sign to show direction
        overhead = f"{row['overhead_%']:>+7.2f}%"

        print(f"{library:<15} | {vanilla_time:<12} | {
              pickleball_time:<12} | {overhead}")

else:
    print("Error: The CSV must contain both 'vanilla' and 'pickleball' versions for comparison.")
