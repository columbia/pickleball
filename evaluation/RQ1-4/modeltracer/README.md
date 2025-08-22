# Model Analysis

## Pre-requisites
- Python 3.11+
- Pip
- Git
- SSH key for huggingface
- Huggingface account
- Dependencies on requirements.txt
- strace2csv from https://github.com/bmwcarit/stracepy



## Folders
- `scripts`: Contains the source code for the analysis.

# Scripts Folder


## Set up
1. Get an SSH key and set it up: https://huggingface.co/docs/hub/en/security-git-ssh

## parse_tracer.py

This file parses the output of the strace files to pinpoint potentially malicious files. It iterates through the folder which contains the tracing results and first runs strace2csv. It then attempts to identify suspicious commands (such as connecting to a socket, etc). We then also read through the original strace file to identify any commands that might be indicative of malicious behaviour. We recommend after running this to still manually check the strace text file, along with the csvs for the strace and sys.settrace to ensure that any malicious behaviours are identified, and to ensure no false positives. 

Before running this file, you first need to install strace2csv from the following repository: https://github.com/bmwcarit/stracepy

To run the file, from the home directory run 
```python -m scripts.parse_tracer```

## pickletools_analysis.py

To find specific payload information for a suspicious model, you can use the ```pickletools_analysis.py``` file. First, download the model file you wish to analyze. Pass in as a command line argument the path to the model file, as well as the desired outfile name and run the program, as follows: ```python -m scripts.pickletools_analysis pytorch_model.bin malicious_results.txt```. The program will output this file into the results directory, and you can see the specific commands in the file that are executed upon loading. NOTE: pickletools does not execute the load of the file, therefore you are safe from any potentially malicious code.


