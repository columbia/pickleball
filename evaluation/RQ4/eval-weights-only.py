#!/usr/bin/env python3
import os
import zipfile
import torch
import tempfile
import hashlib
from pathlib import Path

def create_safe_filename(original_path, method="minimal"):
    """Create a safe output filename that preserves path info"""
    
    path_obj = Path(original_path)
    parts = path_obj.parts
    
    if len(parts) > 1:
        # Include some parent directory info
        safe_parts = []
        for part in parts[-3:]:  # Take last 3 path components
            clean_part = "".join(c for c in part if c.isalnum() or c in ".-_")
            safe_parts.append(clean_part)
        
        safe_name = "_".join(safe_parts)
        
        if safe_name.endswith('.pkl'):
            safe_name = safe_name[:-4]
        
        output_name = f"{safe_name}_{method}.bin"
    else:
        stem = path_obj.stem
        output_name = f"{stem}_{method}.bin"
    
    return output_name

def create_unique_filename(original_path, output_dir, method="minimal"):
    """Create unique filename with path hash if needed"""
    
    base_name = create_safe_filename(original_path, method)
    output_path = os.path.join(output_dir, base_name)
    
    if os.path.exists(output_path):
        path_hash = hashlib.md5(str(original_path).encode()).hexdigest()[:8]
        name_parts = base_name.split('.')
        name_parts[0] += f"__{path_hash}"
        unique_name = ".".join(name_parts)
        output_path = os.path.join(output_dir, unique_name)
    
    return output_path

def create_minimal_pytorch_zip(pkl_file, output_file):
    """Create minimal PyTorch ZIP with PKL embedded"""
    
    try:
        # Create a real PyTorch tensor to get correct structure
        temp_tensor = torch.randn(10, 10)
        temp_file = tempfile.NamedTemporaryFile(suffix='.pt', delete=False)
        temp_file.close()
        
        torch.save(temp_tensor, temp_file.name)
        
        # Replace data.pkl with our malicious PKL
        with zipfile.ZipFile(temp_file.name, 'r') as src_zip:
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as dst_zip:
                
                for item in src_zip.infolist():
                    if item.filename.endswith('data.pkl'):
                        # Replace with our malicious PKL
                        with open(pkl_file, 'rb') as f:
                            dst_zip.writestr(item.filename, f.read())
                    else:
                        # Copy other files as-is
                        data = src_zip.read(item.filename)
                        dst_zip.writestr(item, data)
        
        # Clean up temp file
        os.unlink(temp_file.name)
        return True, None
        
    except Exception as e:
        if 'temp_file' in locals() and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        return False, str(e)

def process_models(model_folder):
    """Process models in a folder and test with weights_only"""
    
    if not os.path.exists(model_folder):
        return 0, 0, 0  # loaded, blocked, error
    
    # Look for model-list.txt inside the model folder
    model_list_path = os.path.join(model_folder, "model-list.txt")
    
    if not os.path.exists(model_list_path):
        return 0, 0, 0
    
    # Use the model folder as base directory
    base_dir = model_folder
    
    # Read file list and create full paths
    with open(model_list_path, 'r') as f:
        relative_paths = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    # Create full paths by concatenating base directory with relative paths
    all_files = []
    for relative_path in relative_paths:
        full_path = os.path.join(base_dir, relative_path)
        all_files.append(full_path)
    
    # Check which files exist and categorize them
    existing_files = []
    
    for file_path in all_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
    
    pkl_files = [f for f in existing_files if f.endswith('.pkl')]
    non_pkl_files = [f for f in existing_files if not f.endswith('.pkl')]
    
    # STEP 1: Wrap PKL files
    wrapped_files = []
    if pkl_files:
        print(f"Preparing {len(pkl_files)} PKL files...")
        output_dir = "pytorch_wrapped_temp"
        os.makedirs(output_dir, exist_ok=True)
        
        for i, pkl_file in enumerate(pkl_files, 1):
            output_file = create_unique_filename(pkl_file, output_dir, "minimal")
            success, error = create_minimal_pytorch_zip(pkl_file, output_file)
            
            if success:
                wrapped_files.append(output_file)
            else:
                pass  # Silently skip failed wraps
    
    # STEP 2: Test all files with weights_only
    test_files = wrapped_files + non_pkl_files
    
    if not test_files:
        return 0, 0, 0
    
    # Test results
    loaded_count = 0
    blocked_count = 0
    error_count = 0
    
    for i, file_path in enumerate(test_files, 1):
        try:
            data = torch.load(file_path, weights_only=True, map_location='cpu')
            print(f"[{i:3d}/{len(test_files)}] LOADED: {file_path}")
            loaded_count += 1
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if any(keyword in error_msg for keyword in [
                'unsafe', 'pickle', 'global', 'reduce', 'builtin', 'eval', 'exec'
            ]):
                print(f"[{i:3d}/{len(test_files)}] BLOCKED: {file_path}")
                blocked_count += 1
            else:
                print(f"[{i:3d}/{len(test_files)}] ERROR: {file_path}")
                error_count += 1
    
    return loaded_count, blocked_count, error_count

def evaluate_weights_only(malicious_folder, benign_folder):
    """Evaluate weights_only on both malicious and benign datasets"""
    
    # Check if both folders exist
    if not os.path.exists(malicious_folder):
        print(f"Error: Malicious model folder '{malicious_folder}' not found.")
        return
    
    if not os.path.exists(benign_folder):
        print(f"Error: Benign model folder '{benign_folder}' not found.")
        return
    
    # Check for model-list.txt in both folders
    malicious_list = os.path.join(malicious_folder, "model-list.txt")
    benign_list = os.path.join(benign_folder, "model-list.txt")
    
    if not os.path.exists(malicious_list):
        print(f"Error: Model list file 'model-list.txt' not found in '{malicious_folder}'.")
        return
    
    if not os.path.exists(benign_list):
        print(f"Error: Model list file 'model-list.txt' not found in '{benign_folder}'.")
        return
    
    print("Starting weights-only evaluation...")
    
    # Process malicious models
    mal_loaded, mal_blocked, mal_error = process_models(malicious_folder)
    
    # Process benign models
    ben_loaded, ben_blocked, ben_error = process_models(benign_folder)
    
    # Calculate confusion matrix metrics
    # For weights_only evaluation:
    # - BLOCKED means the model was detected as potentially malicious 
    # - LOADED means the model was considered safe/benign
    
    # TP = True Positives: Malicious models that were blocked (correctly detected)
    TP = mal_blocked
    
    # TN = True Negatives: Benign models that loaded (correctly identified as safe) 
    TN = ben_loaded
    
    # FP = False Positives: Benign models that were blocked (false alarms)
    FP = ben_blocked
    
    # FN = False Negatives: Malicious models that loaded (missed threats)
    FN = mal_loaded
    
    # Total valid tests (excluding errors)
    total_malicious = TP + FN
    total_benign = TN + FP
    total_valid = TP + TN + FP + FN
    
    if total_valid > 0 and total_malicious > 0 and total_benign > 0:
        fpr = (FP * 100.0) / total_benign
        fnr = (FN * 100.0) / total_malicious
        
        print("")
        print("Tool\t\t#TP\t#TN\t#FP\t#FN\tFPR\tFNR")
        print(f"WeightsOnly\t{TP}\t{TN}\t{FP}\t{FN}\t{fpr:.1f}%\t{fnr:.1f}%")
    else:
        print("Error: Insufficient data for metrics calculation.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python eval-weights-only.py <malicious_model_folder> <benign_model_folder>")
        print()
        print("Arguments:")
        print("  malicious_model_folder - Path to folder containing model-list.txt and malicious model files")
        print("  benign_model_folder    - Path to folder containing model-list.txt and benign model files")
        print()
        print("Note: The script looks for 'model-list.txt' inside each model folder")
        print("      and concatenates relative paths with the model folder path.")
        print()
        print("Example:")
        print("  python eval-weights-only.py /path/to/malicious/models /path/to/benign/models")
        sys.exit(1)
    
    malicious_folder = sys.argv[1]
    benign_folder = sys.argv[2]
    
    evaluate_weights_only(malicious_folder, benign_folder)
