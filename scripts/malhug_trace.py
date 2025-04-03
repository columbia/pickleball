"""
Script for processing MaxHug models 

Can be run on specifically identified repositories (python3 maxhug.py --indir <path/to/models/parent/dir>)
"""
from download_model import generate_trace, get_model_paths
import argparse

import logging
import os, sys, subprocess, json
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
import signal

def modelscan(model_path):
    logging.info("- Modelscaning: %s", model_path)
    model_path = model_path.replace(' ', '\ ')
    # modelscan -p evil_test -r json -o 1.json
    # check=False to supress the return value (which is 1 when a vulnerability is found)
    subprocess.run(f'modelscan -p {model_path} -r json -o {model_path}.modelscan.json', shell=True, check=False)

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Function timed out")

# Set the timeout handler
signal.signal(signal.SIGALRM, timeout_handler)

def run_with_timeout(timeout, func, *args, **kwargs):
    signal.alarm(timeout)  # Set timeout in seconds
    try:
        result = func(*args, **kwargs)
    finally:
        signal.alarm(0)  # Disable the alarm
    return result

def parsetrace(trace_path):
    trace_path = trace_path.replace(' ', '\ ') # escape space in file path
    subprocess.run(f'python3 parsetrace.py {trace_path} > {trace_path}.json', shell=True, check=True)

def process_models(
    indir: str = "",
    run_modelscan: bool=False
) -> None:
    """Process a Hugging Face repository. Defaults behavior is to:
     1. generate a fickling trace of the downloaded models
     2. parse the trace to obtain globals/reduces
     3. run modelscan


    for a model, this script generates:
    - model.trace
    - model.opcode
    - model.json # trace analysis results
    - model.modelscan.json # modelscan results
    """


    # this function could recursively traverse all model files
    model_paths = get_model_paths(indir)

    for model_path in model_paths:
        try:
            run_with_timeout(60, generate_trace, model_path, False, True)
            if run_modelscan:
                modelscan(model_path)

        except TimeoutException:
            print(" - Trace timeout: %s!", model_path)


    result_json = []
    for dirpath, dirnames, filenames in os.walk(indir):
        for filename in filenames:
            if filename.endswith(".opcode"): 
                tracefile = os.path.join(dirpath, filename)
                parsetrace(tracefile)
                result_json.append(tracefile + ".json")
    with open(os.path.join(indir, "trace_jsonfiles.txt"), "w") as fp:
        fp.write("\n".join(result_json))


    '''
    if run_modelscan:
        for dirpath, dirnames, filenames in os.walk(indir):
            for filename in filenames:
                if filename.endswith(modelscan_ext):
                    file_path = os.path.join(dirpath, filename)
                    vulnerable_apis = parse_modelscan_result(file_path)

                    # find those not labled as malicious by modelscan
                    if not vulnerable_apis:
                        logging.warning("**FN case: %s", file_path.rstrip(modelscan_ext))
    '''


def main():
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--indir",
        help=(
            "Parent directory where the MaxHug malicious models saved. "
        ),
    )

    parser.add_argument(
        "--run_modelscan",
        action="store_true",
        default=False,
        help=(
            "Run modelscan if set"
        ),
    )

    args = parser.parse_args()
    if args.indir:
        indir = args.indir
        process_models(indir, args.run_modelscan)
    else:
        logging.error(
            "need to specify the directory for the models to process with "
            "'--indir' argument"
            )
        exit(0)


if __name__ == "__main__":
    main()
