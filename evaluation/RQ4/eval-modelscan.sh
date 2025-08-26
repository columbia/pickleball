#!/bin/bash
# Script for running modelscan on malicious and benign models with confusion matrix metrics

# Usage
if [ $# -ne 2 ]; then
    echo "Usage: $0 <malicious_model_folder> <benign_model_folder>"
    echo ""
    echo "Arguments:"
    echo "  malicious_model_folder - Path to folder containing model-list.txt and malicious model files"
    echo "  benign_model_folder    - Path to folder containing model-list.txt and benign model files"
    echo ""
    echo "Note: The script looks for 'model-list.txt' inside each model folder"
    echo "      and concatenates relative paths with the model folder path."
    echo ""
    echo "Example:"
    echo "  sh $0 /path/to/malicious/models /path/to/benign/models"
    exit 1
fi

MALICIOUS_FOLDER="$1"
BENIGN_FOLDER="$2"

# Check if both model folders exist
if [ ! -d "$MALICIOUS_FOLDER" ]; then
    echo "Error: Malicious model folder '$MALICIOUS_FOLDER' not found."
    exit 1
fi

if [ ! -d "$BENIGN_FOLDER" ]; then
    echo "Error: Benign model folder '$BENIGN_FOLDER' not found."
    exit 1
fi

# Check for model-list.txt in both folders
MALICIOUS_LIST="${MALICIOUS_FOLDER}/model-list.txt"
BENIGN_LIST="${BENIGN_FOLDER}/model-list.txt"

if [ ! -f "$MALICIOUS_LIST" ]; then
    echo "Error: Model list file 'model-list.txt' not found in '$MALICIOUS_FOLDER'."
    exit 1
fi

if [ ! -f "$BENIGN_LIST" ]; then
    echo "Error: Model list file 'model-list.txt' not found in '$BENIGN_FOLDER'."
    exit 1
fi

# Function to scan models in a folder
scan_models() {
    local folder="$1"
    local list_file="$2"
    local label="$3"  # "MALICIOUS" or "BENIGN"
    
    local total_files=$(grep -c . "$list_file")
    local current_file=0
    local detected_malicious=0
    local detected_benign=0
    local error_count=0
    
    # Create temporary file for modelscan output
    local temp_output=$(mktemp)
    
    # Read the file list and scan each file
    while IFS= read -r relative_path; do
        # Skip empty lines and comments
        [ -z "$relative_path" ] && continue
        echo "$relative_path" | grep -q "^[[:space:]]*#" && continue
        
        # Concatenate folder with relative path to get absolute path
        local full_path="${folder}/${relative_path}"
        
        # Increment counter
        current_file=$((current_file + 1))
        
        # Check if file exists
        if [ ! -f "$full_path" ]; then
            error_count=$((error_count + 1))
            continue
        fi
        
        # Run modelscan and capture output
        modelscan -p "$full_path" > "$temp_output" 2>&1
        
        # Analyze the output content to determine if malicious
        if grep -q "No issues found" "$temp_output"; then
            echo "[$current_file/$total_files] BENIGN: $full_path"
            detected_benign=$((detected_benign + 1))
        elif grep -q "CRITICAL\|HIGH\|MEDIUM" "$temp_output" || grep -q "Total Issues: [1-9]" "$temp_output"; then
            echo "[$current_file/$total_files] MALICIOUS: $full_path"
            detected_malicious=$((detected_malicious + 1))
        else
            echo "[$current_file/$total_files] ERROR: $full_path"
            error_count=$((error_count + 1))
        fi
        
    done < "$list_file"
    
    # Clean up temporary file
    rm -f "$temp_output"
    
    # Return results via global variables
    if [ "$label" = "MALICIOUS" ]; then
        MAL_TOTAL=$current_file
        MAL_DETECTED_MAL=$detected_malicious
        MAL_DETECTED_BEN=$detected_benign
        MAL_ERRORS=$error_count
    else
        BEN_TOTAL=$current_file
        BEN_DETECTED_MAL=$detected_malicious
        BEN_DETECTED_BEN=$detected_benign
        BEN_ERRORS=$error_count
    fi
}

echo "Starting modelscan evaluation..."

# Scan malicious models
scan_models "$MALICIOUS_FOLDER" "$MALICIOUS_LIST" "MALICIOUS"

# Scan benign models  
scan_models "$BENIGN_FOLDER" "$BENIGN_LIST" "BENIGN"

# Calculate confusion matrix metrics
# TP = True Positives: Malicious models detected as malicious
TP=$MAL_DETECTED_MAL

# TN = True Negatives: Benign models detected as benign
TN=$BEN_DETECTED_BEN

# FP = False Positives: Benign models detected as malicious
FP=$BEN_DETECTED_MAL

# FN = False Negatives: Malicious models detected as benign
FN=$MAL_DETECTED_BEN

# Total valid tests (excluding errors)
TOTAL_VALID=$((TP + TN + FP + FN))
TOTAL_MALICIOUS=$((TP + FN))
TOTAL_BENIGN=$((TN + FP))


echo ""
printf "Tool\t\t#TP\t#TN\t#FP\t#FN\tFPR\tFNR\n"
printf "ModelScan\t%d\t%d\t%d\t%d\t%.1f%%\t%.1f%%\n" $TP $TN $FP $FN $(awk "BEGIN {printf \"%.1f\", $FP * 100 / $TOTAL_BENIGN}") $(awk "BEGIN {printf \"%.1f\", $FN * 100 / $TOTAL_MALICIOUS}")
