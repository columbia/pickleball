import argparse
import pickle
import signal
from pathlib import Path

import torch
from pklballcheck import collect_attr_stats, verify_loader_was_used


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")


def load_model(model_path, timeout_seconds=30) -> tuple[bool, str]:
    """Load model using pickle or torch based on file extension"""
    model_path = Path(model_path)
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        # Try pickle first, then torch if it fails
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            method = "pickle"
        except Exception:
            model = torch.load(model_path, map_location="cpu")
            method = "torch"
            
        print(f"\033[92mSUCCEEDED ({method}) in {model_path}\033[0m")
        collect_attr_stats(model)
        return True, f"Loaded with {method}: {type(model)}"
        
    except TimeoutError:
        print(f"\033[91mTIMEOUT in {model_path}\033[0m")
        return False, "Operation timed out"
    except Exception as e:
        print(f"\033[91mFAILED in {model_path}\033[0m")
        print(e)
        return False, str(e)
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", help="Path to the model file", required=True)
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")
    
    args = parser.parse_args()
    
    is_success, output = load_model(args.model_path, args.timeout)
    print(output)
    verify_loader_was_used()