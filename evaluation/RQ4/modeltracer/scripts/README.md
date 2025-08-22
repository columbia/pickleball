# Scripts Folder

## model_tracer.py

This file runs sys.settrace and strace. The output is the strace file and a csv for the commands captured by sys.settrace for the model file specified in the command line. Do not run this file outside of some sort of virtual machine, because since we load the model file, we do not want any malicious behaviour to execute on the local machine. Keeping it contained in a virtual machine protects us from any malicious code. To run the file from the home directory, run ```python -m scripts.model_tracer.py path/to/file serialization_method```. The path/to/file should contain the outer repo and the model file inside. This helps to differentiate files, as many can be named the same thing. Please provide the method of serialization (eg tensorflow, numpy, onnx, TorchScript, joblib, dill, pickle, or torch). You will need strace to run this code, so please run it on a Linux machine/virtual env. Please make a results folder for the results from the scripts to go to.


## parse_tracer.py

This file parses the output of the strace files to pinpoint potentially malicious files. It iterates through the folder which contains the tracing results and first runs strace2csv. It then attempts to identify suspicious commands (such as connecting to a socket, etc). We then also read through the original strace file to identify any commands that might be indicative of malicious behaviour. We recommend after running this to still manually check the strace text file, along with the csvs for the strace and sys.settrace to ensure that any malicious behaviours are identified, and to ensure no false positives. For the results of the parsing, please make a folder named malicious_dynamic inside the results directory. This makes finding the final malicious results a bit easier.

Before running this file, you first need to install strace2csv from the following repository: https://github.com/bmwcarit/stracepy

To run the file, from the home directory run 
```python -m scripts.parse_tracer.py```


## pickletools_analysis.py

This file allows you to analyze the bytes of the model file using pickletools. It will show in human readable form the bytes of the pickle file.
