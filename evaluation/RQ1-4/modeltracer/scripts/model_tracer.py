import sys
import opcode
import inspect
import torch
import tensorflow as tf
import numpy as np
import dill
import onnx
import joblib
import pickle

import csv
import pandas as pd
import atexit
from tqdm import tqdm
import os
import logging
import requests
import json
import subprocess

DEBUG = False

def is_callback_invocation(function_code, offset):
    opcode_name = opcode.opname[function_code.co_code[offset]]
    # print(opcode_name)
    # returns true if it is a call (ignore PRECALL to avoid duplicates)
    return "CALL" in opcode_name and "PRECALL" not in opcode_name

def trace_with_csv(writer):
    def analyze(frame, event, arg):
        frame.f_trace_opcodes = True
        # get function code
        function_code = frame.f_code
        offset = frame.f_lasti
        # get function name
        function_name = function_code.co_name
        # if "load_reduce" not in function_name:
        #     return analyze
        # check if the current opcode is a callback invocation
        if not is_callback_invocation(function_code, offset):
            return analyze
        # get line number
        lineno = frame.f_lineno
        source_lines, start = inspect.getsourcelines(function_code)
        actual_line = source_lines[lineno - start]
        variable_values = []
        for name in frame.f_locals:
            variable_values.append(f"{name}={frame.f_locals[name]}")

        # prints them f"{event} --> {function_name}:{lineno}"
        writer.writerow([event, function_name, lineno, actual_line.strip(), variable_values])
        #print(f"{event} --> {function_name}:{lineno} {actual_line.strip()}")
        #print(f"\tVariables:")
        #for v in variable_values:
        #    print(f"\t\t{v}")
        # returns the function itself to track the new scope
        return analyze
    return analyze


def run_strace(full_file_path, straceCommand, outFile):
    '''running strace on loading the model file.
    the flags allow us to capture the following:
    -f: follow any forks in the program
    -tt: absolute timestamps (with microseconds)
    -T: time spent for system calls
    -y: print paths associated with file descriptor arguments
    -yy:  Print all available information associated with file descriptors
    -s: max string size (ours is set to 2048)
    -o: write data to outfile
    '''

    print(straceCommand)
    result = subprocess.run(straceCommand, stderr=subprocess.PIPE)
    
    # Check if the command was successful
    if result.returncode != 0:
        logger.debug(f"Failed to run strace for {full_file_path}: {result.stderr.decode('utf-8')}")

def analyze_files(filepath, method):
    #get the repo and filename from the file path
    repo, file = filepath.rsplit('/', 1)
    #var to track success of analysis
    succeeded = []
    # save the results to a csv file
    filename = file.replace('/', '_') + '_tracer.csv'
    results_file = os.path.join('./results', filename)
    with open(results_file, 'w') as output_csv:
        writer = csv.writer(output_csv)
        writer.writerow(['event', 'function_name', 'line_number', 'line', 'variables'])
        try:
            #prepare outfile path and strace command
            outFileName = repo.replace('/', '_') + '_' + file + '_strace_output.txt'
            outFilePath = os.path.join("./results", outFileName)
            straceCommand = ['strace', '-f', '-tt', '-T', '-y', '-yy', '-s', '2048','-o', outFilePath]

            #we check the method of serialization and load accordingly.
            #we set the tracer around the load so that we only trace the load and nothing else
            #we are wrapping the sys tracer in a try/except block bc it may fail if the backend is in C/C++
            # we do the wrapping so that the strace can still run
            if method == 'tensorflow':
                try:
                    sys.settrace(trace_with_csv(writer))
                    tf.keras.models.load_model(filepath)
                    sys.settrace(None)
                except:
                    pass

                #run strace
                stringLoader = f'import tensorflow; tensorflow.keras.models.load_model("{filepath}")'
                straceCommand.append('python')
                straceCommand.append('-c') 
                straceCommand.append(stringLoader)
                run_strace(filepath, straceCommand, outFilePath)

            if method == 'numpy':
                try:
                    sys.settrace(trace_with_csv(writer))
                    np.load(filepath)
                    sys.settrace(None)
                except:
                    pass

                #run strace
                stringLoader = f'import numpy; numpy.load("{filepath}")'
                straceCommand.append('python')
                straceCommand.append('-c') 
                straceCommand.append(stringLoader)
                run_strace(filepath, straceCommand, outFilePath)

            if method == 'onnx':
                try:
                    sys.settrace(trace_with_csv(writer))
                    onnx.load(filepath)
                    sys.settrace(None)
                except:
                    pass

                #run strace
                stringLoader = f'import onnx; onnx.load("{filepath}")'
                straceCommand.append('python')
                straceCommand.append('-c') 
                straceCommand.append(stringLoader)
                run_strace(filepath, straceCommand, outFilePath)

            if method == 'TorchScript':
                try:
                    sys.settrace(trace_with_csv(writer))
                    torch.jit.load(filepath)
                    sys.settrace(None)
                except:
                    pass

                #run strace
                stringLoader = f'import torch; torch.jit.load("{filepath}")'
                straceCommand.append('python')
                straceCommand.append('-c') 
                straceCommand.append(stringLoader)
                run_strace(filepath, straceCommand, outFilePath)
                        
            if method == 'joblib':
                try:
                    sys.settrace(trace_with_csv(writer))
                    joblib.load(filepath)
                    sys.settrace(None)
                except:
                    pass

                #run strace
                stringLoader = f'import joblib; joblib.load("{filepath}")'
                straceCommand.append('python')
                straceCommand.append('-c') 
                straceCommand.append(stringLoader)
                run_strace(filepath, straceCommand, outFilePath)

            if method == 'dill':
                try:
                    sys.settrace(trace_with_csv(writer))
                    dill.load(filepath)
                    sys.settrace(None)
                except:
                    pass

                #run strace
                stringLoader = f'import dill; dill.load("{filepath}")'
                straceCommand.append('python')
                straceCommand.append('-c') 
                straceCommand.append(stringLoader)
                run_strace(filepath, straceCommand, outFilePath)

            if method == 'pickle':
                '''
                try:
                    sys.settrace(trace_with_csv(writer))
                    pickle.load(filepath)
                    sys.settrace(None)
                except:
                    pass
                '''

                #run strace
                stringLoader = f'import pickle; pickle.load(open("{filepath}", "rb"))'
                straceCommand.append('python')
                straceCommand.append('-c') 
                straceCommand.append(stringLoader)
                run_strace(filepath, straceCommand, outFilePath)

            if method == 'torch':
                '''
                try:
                    sys.settrace(trace_with_csv(writer))
                    torch.load(filepath, map_location=torch.device('cpu'))
                    sys.settrace(None)
                except:
                    pass
                '''

                #run strace
                stringLoader = f'import torch; torch.load("{filepath}", map_location=torch.device("cpu"))'
                straceCommand.append('python')
                straceCommand.append('-c') 
                straceCommand.append(stringLoader)
                run_strace(filepath, straceCommand, outFilePath)
            succeeded.append(repo)
        except Exception as e:
            error = e
            logger.debug(f"Failed to process {file}: {e}")
    #check if our trace actually succeeded. If success, return status, otherwise return status and error message.
    if succeeded:
        return 'success', ''
    else:
        return 'failed', error


if __name__ == '__main__':
    if len(sys.argv) != 3:
            print("Please provide the file and serialization method.")
            sys.exit(1)
    # get file and method from the command line
    file = sys.argv[1]
    method = sys.argv[2]
    log_name = file.replace('/', '_').replace('.', '')

    #check if the entered method is one of the allowed methods
    methods = ['tensorflow', 'numpy', 'onnx', 'TorchScript', 'joblib', 'dill', 'pickle', 'torch']

    if method not in methods:
        print("Please enter one of the following methods: tensorflow, numpy, onnx, TorchScript, joblib, dill, pickle, or torch")
        sys.exit(1)

    logging.basicConfig(level=logging.DEBUG,  # Set the logging level to DEBUG
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define the log message format
                        datefmt='%Y-%m-%d %H:%M:%S',  # Define the date format
                        filename=f'app_dynamic_tracer_{log_name}_{method}.log',  # Log messages to a file named 'app.log'
                        filemode='w')  # Open the log file in write mode
    logger = logging.getLogger(os.path.basename(__file__))

    #if the analysis failed print the error
    status, error = analyze_files(file, method)
    if status == 'failed':
        print(f"Analysis failed for {file}: {error}")
