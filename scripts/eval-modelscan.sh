#!/bin/bash

# Script for running the modelscan tool on many files.
# Takes either a directory containing models ending in .pt, or a file with model names

usage() {
    echo "Usage: $0 -d <directory> -l <logfile>"
    echo "   or: $0 -f <file_with_paths> -l <logfile>"
    exit 1
}

# Parse arguments
while getopts ":d:f:l:" opt; do
    case $opt in
        d) SEARCH_DIR="$OPTARG" ;;
        f) PATH_LIST_FILE="$OPTARG" ;;
        l) LOGFILE="$OPTARG" ;;
        *) usage ;;
    esac
done

# Check required args
if [[ -z "$LOGFILE" ]]; then
    echo "Error: Log file must be specified with -l"
    usage
fi

if [[ -n "$SEARCH_DIR" && -n "$PATH_LIST_FILE" ]]; then
    echo "Error: Specify either a directory (-d) OR a file list (-f), not both."
    usage
elif [[ -z "$SEARCH_DIR" && -z "$PATH_LIST_FILE" ]]; then
    echo "Error: You must specify either a directory (-d) or a file list (-f)."
    usage
fi

> "$LOGFILE"  # Clear the log file at the start

# Build the list of files to scan
if [[ -n "$SEARCH_DIR" ]]; then
    FILES=$(find "$SEARCH_DIR" -type f -name "*.pt")
elif [[ -n "$PATH_LIST_FILE" ]]; then
    if [[ ! -f "$PATH_LIST_FILE" ]]; then
        echo "Error: File list '$PATH_LIST_FILE' not found."
        exit 1
    fi
    FILES=$(cat "$PATH_LIST_FILE")
fi

# Scan files
echo "$FILES" | while read -r file; do
    if [[ -z "$file" ]]; then continue; fi
    echo "Scanning: $file"
    
    modelscan -p "$file"
    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "$file : BENIGN" >> "$LOGFILE"
    elif [ $exit_code -eq 1 ]; then
        echo "$file : MALICIOUS" >> "$LOGFILE"
    else
        echo "$file : ERROR (exit code $exit_code)" >> "$LOGFILE"
    fi
done
