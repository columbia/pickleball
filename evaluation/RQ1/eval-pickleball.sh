#!/bin/bash

# Function to detect model type based on file extension
detect_model_type() {
    local model_path="$1"
    local extension="${model_path##*.}"

    case "$extension" in
        "bin"|"pth"|"pt")
            echo "torch"
            ;;
        "pkl"|"pickle")
            echo "pickle"
            ;;
        *)
            echo "torch"
            ;;
    esac
}

# Function to load model and check for blocking keyword
load_model() {
    local model_path="$1"
    local image="$2"
    local timeout_seconds="$3"
    local model_name="$4"
    local mode="$5"

    local host_path=$(realpath "$model_path")
    local output

    if [ "$mode" = "torch" ]; then
        output=$(docker run --rm -v "${host_path}:/app/model/${model_name}" "$image" bash -c "timeout $timeout_seconds python3 -c 'import torch; torch.load(\"/app/model/$model_name\", map_location=\"cpu\")'" 2>&1)
    elif [ "$mode" = "pickle" ]; then
        # Try pickle first
        output=$(docker run --rm -v "${host_path}:/app/model/${model_name}" "$image" bash -c "timeout $timeout_seconds python3 -c 'import pickle; pickle.load(open(\"/app/model/$model_name\", \"rb\"))'" 2>&1)
        local pickle_exit=$?
        
        # If pickle failed, try torch
        if [ $pickle_exit -ne 0 ]; then
            torch_output=$(docker run --rm -v "${host_path}:/app/model/${model_name}" "$image" bash -c "timeout $timeout_seconds python3 -c 'import torch; torch.load(\"/app/model/$model_name\", map_location=\"cpu\")'" 2>&1)
            output="${output}\n${torch_output}"
        fi
    fi

    # Check for blocking keyword
    if echo "$output" | grep -q "Exception: Tried to access"; then
        echo "1"  # Blocked
    else
        echo "0"  # Loaded
    fi
}

# Main script
main() {
    local input_file="$1"
    local image="$2"
    local timeout="${3:-300}"

    if [ ! -f "$input_file" ]; then
        echo "Error: Input file '$input_file' not found"
        exit 1
    fi

    local total_models=0
    local blocked_models=0

    while IFS= read -r model_path; do
        # Skip empty lines and comments
        [ -z "$model_path" ] && continue
        echo "$model_path" | grep -q "^[[:space:]]*#" && continue

        total_models=$((total_models + 1))

        # Detect model type
        local model_type=$(detect_model_type "$model_path")
        
        echo "Model $total_models: Processing $model_path"

        # Load model and check if blocked
        local result=$(load_model "$model_path" "$image" "$timeout" "testmodel" "$model_type")
        
        if [ "$result" = "1" ]; then
            blocked_models=$((blocked_models + 1))
            echo "Blocked"
        else
            echo "Loaded"
        fi

    done < "$input_file"

    # Final summary
    local loaded_models=$((total_models - blocked_models))
    echo ""
    echo "=== SUMMARY ==="
    echo "Total model tested: $total_models"
    echo "Loaded: $loaded_models"
    echo "Blocked: $blocked_models"

    if [ $total_models -gt 0 ]; then
        local blocked_rate=$((blocked_models * 100 / total_models))
        local loaded_rate=$((loaded_models * 100 / total_models))
        echo ""
        echo "PERCENTAGES:"
        echo "Loaded: $loaded_rate% ($loaded_models/$total_models models)"
        echo "Blocked: $blocked_rate% ($blocked_models/$total_models models)"
    fi
}

# Usage
if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    echo "Usage: $0 <model_list_file> <docker_image> [timeout_seconds]"
    echo ""
    echo "Arguments:"
    echo "  model_list_file - File containing one model path per line"
    echo "  docker_image    - Docker image name (e.g., myimage:latest)"
    echo "  timeout_seconds - Optional timeout in seconds (default: 300)"
    echo ""
    echo "Examples:"
    echo "  $0 model_paths.txt myimage:latest"
    echo "  $0 model_paths.txt myimage:latest 600"
    exit 1
fi

main "$1" "$2" "$3"
