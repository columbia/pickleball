import argparse
from download_model import generate_trace, get_model_paths

import logging
import os, sys, subprocess, json
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def modelscan(model_path):
    logging.info("- Modelscaning: %s", model_path)
    model_path = model_path.replace(' ', '\ ')
    # modelscan -p evil_test -r json -o 1.json
    # check=False to supress the return value (which is 1 when a vulnerability is found)
    try:
        subprocess.run(f'modelscan -p {model_path} -r json -o {model_path}.modelscan.json', shell=True, check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logging.error("--* Modelscaning exit: %d", e.returncode)


def main():
    """Main function. Collect command line arguments and begin"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--indir",
        help=(
            "input dir"
        ),
    )
    args = parser.parse_args()
    model_paths = get_model_paths(args.indir)

    for model_path in model_paths:
        modelscan(model_path)

if __name__ == "__main__":
    main()
