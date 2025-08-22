#!/bin/bash
# Script for running modelscan on a list of files - screen output only

usage() {
    echo "Usage: $0 -f <file_with_paths>"
    echo "  -f: File containing list of model paths (one per line)"
    exit 1
}

# Parse arguments
while getopts ":f:" opt; do
    case $opt in
        f) PATH_LIST_FILE="$OPTARG" ;;
        *) usage ;;
    esac
done

# Check required args
if [ -z "$PATH_LIST_FILE" ]; then
    echo "Error: File list must be specified with -f"
    usage
fi

# Check if the file list exists
if [ ! -f "$PATH_LIST_FILE" ]; then
    echo "Error: File list '$PATH_LIST_FILE' not found."
    exit 1
fi

echo "Starting modelscan..."
echo ""

# Counter for progress
total_files=$(wc -l < "$PATH_LIST_FILE")
current_file=0
benign_count=0
malicious_count=0
error_count=0

# Create temporary file for modelscan output
temp_output=$(mktemp)

# Read the file list and scan each file
while IFS= read -r file; do
    # Skip empty lines
    if [ -z "$file" ]; then
        continue
    fi
    
    # Increment counter
    current_file=$((current_file + 1))
    
    # Check if file exists
    if [ ! -f "$file" ]; then
        echo "[$current_file/$total_files] FILE_NOT_FOUND: $file"
        error_count=$((error_count + 1))
        continue
    fi
    
    # Run modelscan and capture output
    modelscan -p "$file" > "$temp_output" 2>&1
    
    # Analyze the output content to determine if malicious
    if grep -q "No issues found" "$temp_output"; then
        echo "[$current_file/$total_files] BENIGN: $file"
        benign_count=$((benign_count + 1))
    elif grep -q "CRITICAL\|HIGH\|MEDIUM" "$temp_output" || grep -q "Total Issues: [1-9]" "$temp_output"; then
        echo "[$current_file/$total_files] MALICIOUS: $file"
        malicious_count=$((malicious_count + 1))
    else
        echo "[$current_file/$total_files] ERROR: $file"
        error_count=$((error_count + 1))
    fi
    
done < "$PATH_LIST_FILE"

# Clean up temporary file
rm -f "$temp_output"

echo "=========================================="
echo "SUMMARY:"
echo "   Total scanned: $total_files"
echo "   Benign: $benign_count"
echo "   Malicious: $malicious_count"
echo ""

# Show percentages with one decimal place
if [ $total_files -gt 0 ]; then
    malicious_pct=$(awk "BEGIN {printf \"%.1f\", $malicious_count * 100 / $total_files}")
    benign_pct=$(awk "BEGIN {printf \"%.1f\", $benign_count * 100 / $total_files}")
    error_pct=$(awk "BEGIN {printf \"%.1f\", $error_count * 100 / $total_files}")
    
    echo "PERCENTAGES:"
    echo "   Benign: ${benign_pct}%"
    echo "   Malicious: ${malicious_pct}%"
fi
