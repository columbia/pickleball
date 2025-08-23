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
            echo 'FOUND UNSAFE: Model caused hanging/infinite execution in $mode mode'
            exit 124
        elif [ \$tracer_exit -eq 0 ]; then
            timeout $timeout_seconds python3 -m scripts.parse_tracer
            parser_exit=\$?

            if [ \$parser_exit -eq 124 ]; then
                echo 'TIMEOUT_MALICIOUS: parse_tracer exceeded timeout'
                echo 'FOUND UNSAFE: Parser caused hanging/infinite execution'
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
    local timeout_seconds="${3:-300}"  # Default 5 minutes timeout

    # Check if model file exists
    if [ ! -f "$model_path" ]; then
        echo "Model file not found: $model_path"
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

# Main script
main() {
    local input_file="$1"
    local image="$2"
    local timeout="${3:-300}"  # Default 5 minutes, can be overridden

    if [ ! -f "$input_file" ]; then
        echo "Error: Input file '$input_file' not found"
        exit 1
    fi

    local total_models=0
    local unsafe_models=0
    local torch_models=0
    local pickle_models=0
    local timeout_models=0
    local killed_models=0
    local failed_models=0

    while IFS= read -r model_path; do
        # Skip empty lines and comments
        [ -z "$model_path" ] && continue
        echo "$model_path" | grep -q "^[[:space:]]*#" && continue

        total_models=$((total_models + 1))

        # Count model types
        local model_type=$(detect_model_type "$model_path")
        if [ "$model_type" = "torch" ]; then
            torch_models=$((torch_models + 1))
        else
            pickle_models=$((pickle_models + 1))
        fi

        echo "Model $total_models: Processing $model_path"

        if process_model "$model_path" "$image" "$timeout"; then
            # Check if unsafe was found
            if [ -f /tmp/unsafe_count_$$ ]; then
                local model_is_unsafe=$(cat /tmp/unsafe_count_$$)
                unsafe_models=$((unsafe_models + model_is_unsafe))
                if [ $model_is_unsafe -eq 1 ]; then
                    echo "Found UNSAFE"
                else
                    echo "Safe"
                fi
                rm -f /tmp/unsafe_count_$$
            else
                echo "Safe"
            fi
        else
            local exit_code=$?
            if [ $exit_code -eq 124 ]; then
                timeout_models=$((timeout_models + 1))
                unsafe_models=$((unsafe_models + 1))  # Count timeout as unsafe
                echo "Found UNSAFE (timeout)"
            elif [ $exit_code -eq 137 ]; then
                killed_models=$((killed_models + 1))
                unsafe_models=$((unsafe_models + 1))  # Count killed as unsafe
                echo "Found UNSAFE (killed)"
            else
                failed_models=$((failed_models + 1))
                echo "Failed"
            fi
            # Clean up temp file if it exists
            rm -f /tmp/unsafe_count_$$
        fi

    done < "$input_file"

    # Final summary
    echo ""
    echo "=== FINAL SUMMARY ==="
    echo "Total models processed: $total_models"
    echo "UNSAFE models: $unsafe_models"
    echo "  - Timeout (malicious): $timeout_models"
    echo "  - Killed (malicious): $killed_models"
    echo "  - Other unsafe: $((unsafe_models - timeout_models - killed_models))"
    echo "Safe models: $((total_models - unsafe_models - failed_models))"

    if [ $total_models -gt 0 ]; then
        local unsafe_rate=$((unsafe_models * 100 / total_models))
        local safe_rate=$(((total_models - unsafe_models - failed_models) * 100 / total_models))
        echo ""
        echo "UNSAFE rate: $unsafe_rate% ($unsafe_models/$total_models models)"
        echo "Safe rate: $safe_rate% ($(($total_models - unsafe_models - failed_models))/$total_models models)"
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
    echo "Supported model formats: .bin, .pth, .pt (torch), .pkl, .pickle (pickle)"
    echo ""
    echo "Examples:"
    echo "  $0 model_paths.txt myimage:latest"
    echo "  $0 model_paths.txt myimage:latest 600  # 10 minute timeout"
    exit 1
fi

main "$1" "$2" "$3"
