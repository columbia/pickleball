#!/bin/bash

# Usage: ./move_subdirs.sh subdir_list.txt /path/to/source /path/to/destination

# Get arguments
SUBDIR_LIST_FILE="$1"
SOURCE_DIR="$2"
DEST_DIR="$3"

# Check if all arguments are provided
if [[ -z "$SUBDIR_LIST_FILE" || -z "$SOURCE_DIR" || -z "$DEST_DIR" ]]; then
    echo "Usage: $0 subdir_list.txt /path/to/source /path/to/destination"
    exit 1
fi

# Make sure the destination directory exists
mkdir -p "$DEST_DIR"

# Loop over each line in the subdir list file
while IFS= read -r subdir; do

    processed_subdir=$(echo "$subdir" | sed 's/\//-/g')

    # Check if the subdirectory exists in the source directory
    if [[ -d "$SOURCE_DIR/$processed_subdir" ]]; then
        echo "Copying $processed_subdir from $SOURCE_DIR to $DEST_DIR"
        cp -r "$SOURCE_DIR/$processed_subdir" "$DEST_DIR/"
    else
        echo "Warning: $processed_subdir does not exist in $SOURCE_DIR"
    fi
done < "$SUBDIR_LIST_FILE"
