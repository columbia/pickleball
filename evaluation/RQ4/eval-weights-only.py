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

def wrap_and_test_models(file_list_path, output_dir="pytorch_wrapped"):
    """Complete pipeline: wrap PKL files and test with weights_only"""
    
    if not os.path.exists(file_list_path):
        print(f"Error: File list '{file_list_path}' not found.")
        return
    
    # Read file list
    with open(file_list_path, 'r') as f:
        all_files = [line.strip() for line in f if line.strip()]
    
    pkl_files = [f for f in all_files if f.endswith('.pkl')]
    non_pkl_files = [f for f in all_files if not f.endswith('.pkl')]
    
    print(f"Found {len(all_files)} total files ({len(pkl_files)} PKL, {len(non_pkl_files)} non-PKL)")
    print()
    
    # STEP 1: Wrap PKL files
    wrapped_files = []
    if pkl_files:
        print("STEP 1: Wrapping PKL files...")
        os.makedirs(output_dir, exist_ok=True)
        
        wrap_success = 0
        wrap_failed = 0
        
        for i, pkl_file in enumerate(pkl_files, 1):
            if not os.path.exists(pkl_file):
                print(f"[{i:3d}/{len(pkl_files)}] WRAP_NOT_FOUND: {pkl_file}")
                wrap_failed += 1
                continue
            
            output_file = create_unique_filename(pkl_file, output_dir, "minimal")
            success, error = create_minimal_pytorch_zip(pkl_file, output_file)
            
            if success:
                print(f"[{i:3d}/{len(pkl_files)}] WRAP_SUCCESS: {pkl_file} -> {output_file}")
                wrapped_files.append(output_file)
                wrap_success += 1
            else:
                print(f"[{i:3d}/{len(pkl_files)}] WRAP_FAILED: {pkl_file}")
                wrap_failed += 1
        
        print(f"Wrapping complete: {wrap_success} success, {wrap_failed} failed")
        print()
    
    # STEP 2: Test all files with weights_only
    print("STEP 2: Testing with weights_only=True...")
    
    test_files = wrapped_files + non_pkl_files
    
    if not test_files:
        print("No files to test.")
        return
    
    # Test results
    loaded_count = 0
    blocked_count = 0
    error_count = 0
    not_found_count = 0
    
    for i, file_path in enumerate(test_files, 1):
        if not os.path.exists(file_path):
            print(f"[{i:3d}/{len(test_files)}] FILE_NOT_FOUND: {file_path}")
            not_found_count += 1
            continue
        
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
    
    # Final Results
    print()
    print("=== SUMMARY ===" )
    
    total_tested = len(test_files)
    total_valid = total_tested - not_found_count
    
    print(f"Total model tested: {total_tested}")
    
    print(f"Loaded: {loaded_count}")
    print(f"Blocked: {blocked_count}")
    print()
    
    if total_valid > 0:
        safe_pct = (loaded_count / total_valid) * 100
        unsafe_pct = (blocked_count / total_valid) * 100
        
        print(f"PERCENTAGES:")
        print(f"Loaded: {safe_pct:.1f}%")
        print(f"Blocked: {unsafe_pct:.1f}%")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python wrap_and_test_simple.py <file_list.txt>")
        sys.exit(1)
    
    file_list = sys.argv[1]
    wrap_and_test_models(file_list)
