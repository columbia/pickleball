"""
Script for processing MaxHug models 

Can be run on specifically identified repositories (python3 maxhug.py --indir <path/to/models/parent/dir>)
"""
from download_model import generate_trace, get_model_paths
import argparse

import logging
import os, sys, subprocess, json
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def process_maxhug(
    indir: str = ""
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
        generate_trace(model_path, delete_after_tracing=False)

    def parsetrace(trace_path):
        trace_path = trace_path.replace(' ', '\ ') # escape space in file path
        subprocess.run(f'python3 parsetrace.py {trace_path} > {trace_path}.json', shell=True, check=True)


    for dirpath, dirnames, filenames in os.walk(indir):
        for filename in filenames:
            if filename.endswith(".opcode"): 
                tracefile = os.path.join(dirpath, filename)
                parsetrace(tracefile)


    def modelscan(model_path):
        logging.info("- Modelscaning: %s", model_path)
        model_path = model_path.replace(' ', '\ ')
        # modelscan -p evil_test -r json -o 1.json
        # check=False to supress the return value (which is 1 when a vulnerability is found)
        subprocess.run(f'modelscan -p {model_path} -r json -o {model_path}.modelscan.json', shell=True, check=False)

    for model_path in model_paths:
        modelscan(model_path)

    def result_analysis(indir):
        modelscan_ext = ".modelscan.json"
        tracescan_ext = ".opcode.json"
        common_modules = ["torch", "transformers", "collections.OrderedDict"]

        modelscan_fns = {}


        def parse_tracescan_result(filename):
            with open(filename, 'r') as fp:
                data = json.load(fp)

                return [g for g in data["globals"] if not any(g.startswith(prefix) for prefix in common_modules)]
            return []


        def parse_modelscan_result(filename):
            with open(filename, 'r') as fp:
                data = json.load(fp)
                issues = [i["module"] + "." + i["operator"] for i in data["issues"]]
                return issues
            return []

        def check_trace(model_path):
            tracescan_file = model_path + tracescan_ext
            if os.path.exists(tracescan_file):
                gs = parse_tracescan_result(tracescan_file)
                if gs:
                    logging.warning("**** APIs: %s", ', '.join(gs))
                    return
            logging.warning("**** Trace not generated successfully")


        for dirpath, dirnames, filenames in os.walk(indir):
            for filename in filenames:
                if filename.endswith(modelscan_ext):
                    file_path = os.path.join(dirpath, filename)
                    vulnerable_apis = parse_modelscan_result(file_path)

                    # find those not labled as malicious by modelscan
                    if not vulnerable_apis:
                        logging.warning("**FN case: %s", file_path.rstrip(modelscan_ext))
                        check_trace(file_path.rstrip(modelscan_ext))

    result_analysis(indir)


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
        "--outdir",
        help=(
            "Output parent directory where the processed model will be saved. "
            "If not set, the current directory will be used."
        ),
    )

    args = parser.parse_args()
    if args.indir:
        indir = args.indir
        process_maxhug(indir)
    else:
        logging.error(
            "need to specify the directory for maxhug models to process with "
            "'--indir' argument"
            )
        exit(0)



if __name__ == "__main__":
    main()
