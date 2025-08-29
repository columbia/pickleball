#!/bin/bash

# Load environment variables - search current, parent, and grandparent directories
if [ -f .env ]; then
    source .env
elif [ -f ../.env ]; then
    source ../.env
elif [ -f ../../.env ]; then
    source ../../.env
else
    echo "Error: No .env file found in current directory, parent directory, or grandparent directory"
    echo "Expected environment variables:"
    echo "  BENIGN_MODELS=<path to benign models>"
    echo "  MALICIOUS_MODELS=<path to malicious models>"
    echo "  DATASETS=<path to datasets>"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$BENIGN_MODELS" ] || [ -z "$MALICIOUS_MODELS" ]; then
    echo "Error: Required environment variables not set"
    echo "Please ensure your .env file contains:"
    echo "  BENIGN_MODELS=<path to benign models>"
    echo "  MALICIOUS_MODELS=<path to malicious models>"
    exit 1
fi

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
            # Default to torch for unknown extensions
            echo "torch"
            ;;
    esac
}

# Reusable function to run model tracer with specific mode
run_model_tracer() {
    local model_path="$1"
    local image="$2"
    local timeout_seconds="$3"
    local model_name="$4"
    local mode="$5"  # "pickle" or "torch"

    local output
    host_path=$(realpath "$model_path")
    output=$(docker run --rm \
        -e PYTHONBREAKPOINT=0 \
	-v "${host_path}:/app/model/${model_name}"  \
        "$image" bash -c "

        timeout $timeout_seconds python3 -m scripts.model_tracer /app/model/$model_name $mode
        tracer_exit=\$?

        if [ \$tracer_exit -eq 124 ]; then
            echo 'TIMEOUT_MALICIOUS: model_tracer ($mode mode) exceeded timeout'
            echo 'Unsafe: Model caused hanging/infinite execution in $mode mode'
            exit 124
        elif [ \$tracer_exit -eq 0 ]; then
            timeout $timeout_seconds python3 -m scripts.parse_tracer
            parser_exit=\$?

            if [ \$parser_exit -eq 124 ]; then
                echo 'TIMEOUT_MALICIOUS: parse_tracer exceeded timeout'
                echo 'Unsafe: Parser caused hanging/infinite execution'
                exit 124
            else
                exit \$parser_exit
            fi
        else
            echo 'model_tracer ($mode mode) failed with exit code:' \$tracer_exit
            exit \$tracer_exit
        fi
    " 2>&1 < /dev/null)

    local exit_code=$?
    local unsafe_count=$(echo "$output" | grep -c -E "(FOUND UNSAFE|TIMEOUT_MALICIOUS|KILLED_MALICIOUS)")

    # Return results via global variables (since bash functions can't return complex data easily)
    TRACER_OUTPUT="$output"
    TRACER_EXIT_CODE=$exit_code
    TRACER_UNSAFE_COUNT=$unsafe_count
}

process_model() {
    local model_path="$1"
    local image="$2"
    local timeout_seconds=100  # Fixed timeout of 100 seconds

    # Check if model file exists
    if [ ! -f "$model_path" ]; then
        return 1
    fi

    # Detect model type
    local model_type=$(detect_model_type "$model_path")
    local model_name=testmodel

    local total_unsafe=0
    local overall_exit_code=0

    # For pickle files, try both pickle and torch modes
    if [ "$model_type" = "pickle" ]; then
        # Try pickle mode first
        run_model_tracer "$model_path" "$image" "$timeout_seconds" "$model_name" "pickle"

        local pickle_exit_code=$TRACER_EXIT_CODE
        local pickle_unsafe=$TRACER_UNSAFE_COUNT

        total_unsafe=$((total_unsafe + pickle_unsafe))

        # If pickle mode didn't find unsafe issues, also try torch mode
        if [ $pickle_unsafe -eq 0 ] && [ $pickle_exit_code -eq 0 ]; then
            run_model_tracer "$model_path" "$image" "$timeout_seconds" "$model_name" "torch"

            local torch_exit_code=$TRACER_EXIT_CODE
            local torch_unsafe=$TRACER_UNSAFE_COUNT

            total_unsafe=$((total_unsafe + torch_unsafe))

            # Overall exit code is success if at least one mode succeeded
            if [ $torch_exit_code -ne 0 ]; then
                overall_exit_code=$torch_exit_code
            fi
        else
            # Pickle mode found issues or failed
            overall_exit_code=$pickle_exit_code
        fi

    else
        # For non-pickle files, use the detected type (torch)
        run_model_tracer "$model_path" "$image" "$timeout_seconds" "$model_name" "$model_type"

        overall_exit_code=$TRACER_EXIT_CODE
        total_unsafe=$TRACER_UNSAFE_COUNT
    fi

    # Store whether this model is unsafe (1 if any unsafe found, 0 if none)
    local is_unsafe=0
    if [ $total_unsafe -gt 0 ]; then
        is_unsafe=1
    fi

    echo "$is_unsafe" > /tmp/unsafe_count_$$
    return $overall_exit_code
}

# Function to trace models in a folder
trace_models() {
    local image="$1"
    local folder="$2"
    local list_file="$3"
    local label="$4"  # "MALICIOUS" or "BENIGN"

    local timeout=100  # Fixed timeout of 100 seconds

    local total_files=$(grep -c . "$list_file")
    local current_file=0
    local detected_unsafe=0
    local detected_safe=0
    local failed_count=0

    # Read the file list and trace each file
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
            failed_count=$((failed_count + 1))
            continue
        fi

        if process_model "$full_path" "$image" "$timeout"; then
            # Check if unsafe was found
            if [ -f /tmp/unsafe_count_$$ ]; then
                local model_is_unsafe=$(cat /tmp/unsafe_count_$$)
                if [ $model_is_unsafe -eq 1 ]; then
                    echo "[$current_file/$total_files] UNSAFE: $full_path"
                    detected_unsafe=$((detected_unsafe + 1))
                else
                    echo "[$current_file/$total_files] SAFE: $full_path"
                    detected_safe=$((detected_safe + 1))
                fi
                rm -f /tmp/unsafe_count_$$
            else
                echo "[$current_file/$total_files] SAFE: $full_path"
                detected_safe=$((detected_safe + 1))
            fi
        else
            local exit_code=$?
            if [ $exit_code -eq 124 ] || [ $exit_code -eq 137 ]; then
                echo "[$current_file/$total_files] UNSAFE: $full_path"
                detected_unsafe=$((detected_unsafe + 1))  # Count timeout/killed as unsafe
            else
                echo "[$current_file/$total_files] FAILED: $full_path"
                failed_count=$((failed_count + 1))
            fi
            # Clean up temp file if it exists
            rm -f /tmp/unsafe_count_$$
        fi

    done < "$list_file"

    # Return results via global variables
    if [ "$label" = "MALICIOUS" ]; then
        MAL_TOTAL=$current_file
        MAL_DETECTED_UNSAFE=$detected_unsafe
        MAL_DETECTED_SAFE=$detected_safe
        MAL_FAILED=$failed_count
    else
        BEN_TOTAL=$current_file
        BEN_DETECTED_UNSAFE=$detected_unsafe
        BEN_DETECTED_SAFE=$detected_safe
        BEN_FAILED=$failed_count
    fi
}

# Main script
main() {
    local image="modeltracer:latest"
    local malicious_folder="$MALICIOUS_MODELS"
    local benign_folder="$BENIGN_MODELS"

    # Check if both model folders exist
    if [ ! -d "$malicious_folder" ]; then
        echo "Error: Malicious model folder '$malicious_folder' not found"
        exit 1
    fi

    if [ ! -d "$benign_folder" ]; then
        echo "Error: Benign model folder '$benign_folder' not found"
        exit 1
    fi

    # Check for model-list.txt in both folders
    local malicious_list="${malicious_folder}/model-list.txt"
    local benign_list="${benign_folder}/model-list.txt"

    if [ ! -f "$malicious_list" ]; then
        echo "Error: Model list file 'model-list.txt' not found in '$malicious_folder'"
        exit 1
    fi

    if [ ! -f "$benign_list" ]; then
        echo "Error: Model list file 'model-list.txt' not found in '$benign_folder'"
        exit 1
    fi

    echo "Starting modeltracer evaluation..."
    echo "Using environment variables:"
    echo "  BENIGN_MODELS=$BENIGN_MODELS"
    echo "  MALICIOUS_MODELS=$MALICIOUS_MODELS"
    echo "Using Docker image: modeltracer:latest"
    echo ""

    # Trace malicious models
    trace_models "$image" "$malicious_folder" "$malicious_list" "MALICIOUS"

    # Trace benign models
    trace_models "$image" "$benign_folder" "$benign_list" "BENIGN"

    # Calculate confusion matrix metrics
    # TP = True Positives: Malicious models detected as unsafe
    TP=$MAL_DETECTED_UNSAFE

    # TN = True Negatives: Benign models detected as safe
    TN=$BEN_DETECTED_SAFE

    # FP = False Positives: Benign models detected as unsafe
    FP=$BEN_DETECTED_UNSAFE

    # FN = False Negatives: Malicious models detected as safe
    FN=$MAL_DETECTED_SAFE

    # Total valid tests (excluding failures)
    TOTAL_VALID=$((TP + TN + FP + FN))
    TOTAL_MALICIOUS=$((TP + FN))
    TOTAL_BENIGN=$((TN + FP))

    echo ""
    printf "Tool\t\t#TP\t#TN\t#FP\t#FN\tFPR\tFNR\n"
    printf "ModelTracer\t%d\t%d\t%d\t%d\t%.1f%%\t%.1f%%\n" $TP $TN $FP $FN $(awk "BEGIN {printf \"%.1f\", $FP * 100 / $TOTAL_BENIGN}") $(awk "BEGIN {printf \"%.1f\", $FN * 100 / $TOTAL_MALICIOUS}")
}

# Usage
if [ $# -ne 0 ]; then
    echo "Usage: $0"
    echo ""
    echo "Environment variables (from .env file):"
    echo "  BENIGN_MODELS=<path to benign models>"
    echo "  MALICIOUS_MODELS=<path to malicious models>"
    echo ""
    echo "Note: The script uses Docker image 'modeltracer:latest' and a fixed timeout of 100 seconds."
    echo "      It looks for 'model-list.txt' inside each model folder."
    echo ""
    echo "Supported model formats: .bin, .pth, .pt (torch), .pkl, .pickle (pickle)"
    echo ""
    echo "Example:"
    echo "  $0"
    exit 1
fi

main