import os
import pandas as pd
import csv
import subprocess
import logging




included_files = ['strace_output.txt', '_tracer.csv', 'strace.csv' ]
commands_of_interest = ['execve', 'connect', 'socket', 'chmod']


def run_strac2csv(full_file_path, outfile):
    command = ['strace2csv', full_file_path, '--out', outfile]
    result = subprocess.run(command)
    
    if result.returncode != 0:
        logger.debug(f"Failed to run strace for {full_file_path}: {result.stderr}")



def analyse_files(): 
    #first we find all the strace files. we need to convert them to csv using strace2csv
    all_files = os.listdir('./results')
    strace_files = [filename for filename in all_files if 'strace_output.txt'in filename]
    for filename in strace_files:
        if 'strace_output.txt' in filename:
            idx = filename.find('strace_output.txt')
            outfile = filename[:idx] + 'strace.csv'
            outPath = os.path.join('./results', *outfile.split("/"))
            filepath = os.path.join('./results', *filename.split("/"))
            run_strac2csv(filepath, outPath)
    #our list of clean repos
    clean_repos = []
    #we rereun os.listdir to get all the files including the csv strace files. now we have the full list of files to analyse
    all_files = os.listdir('./results')
    # we first want to go thru the strace csvs to find any sockets or any unexpected execv's
    strace_files_anlayse = [os.path.join('./results', *filename.split("/")) for filename in all_files if 'strace.csv'in filename]
    for filename in strace_files_anlayse:
        if '_strace.csv' in filename:
            try:
                df = pd.read_csv(filename)
                '''there will always be one execve call in the very first line. this is definitely benign, so we 
                can ignore it. We want to get the rows in the df that have a suspicious syscall, namely the ones
                in the commands_of_interest list. if the df is not empty, eg contains calls to these suspicious calls,
                we write the df to a csv. Otherwise, we add the model to a list of clean repos.'''
                first_execve_index = df[df['syscall'] == 'execve'].index[0]
                df = df.drop(first_execve_index)
                filtered = df[df['syscall'].isin(commands_of_interest)]
                if filtered.empty:
                    idx = filename.find('_strace.csv')
                    last_slash = filename.rfind('/')
                    model_name = filename[last_slash+1:idx]
                    clean_repos.append(model_name)
                else:
                    print('FOUND UNSAFE')
                    malicious_dir = './results' +  '/malicious_dynamic/'
                    idx = filename.find('_strace.csv')
                    last_slash = filename.rfind('/')
                    model_name = filename[last_slash+1:idx] + '_malicious_results.csv'
                    malicious_filepath =  os.path.join(malicious_dir, *model_name.split('/'))
                    print(malicious_filepath)
                    filtered.to_csv(malicious_filepath)
            except pd.errors.EmptyDataError:
                continue
    return clean_repos
            

def parse_strace_text():
    malicious_commands = []
    searching = ['exec(', 'eval(', 'connect(', 'socket(']
    all_files = os.listdir('./results')
    # we first want to go thru the strace csvs to find any sockets or any unexpected execv's
    strace_files_anlayse = [os.path.join('./results', *filename.split("/")) for filename in all_files if 'strace_output.txt'in filename]
    for file in strace_files_anlayse:
        with open (file, 'r') as f:
            for line in f:
                if any(s in line for s in searching):
                    malicious_commands.append(line)
        #for each command for each file, if there is something malicious we will write it to a file
        malicious_dir = './results' / 'malicious_dynamic/'
        idx = file.find('strace_output.txt')
        last_slash = file.rfind('/')
        model_name = file[last_slash+1:idx] + 'malicious_strace.txt'
        malicious_filepath =  os.path.join(malicious_dir, *model_name.split('/'))
        with open(malicious_filepath, 'w') as f:
            for line in malicious_commands:
                f.write(f"{line}\n")
                f.write('\n')



if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG,  # Set the logging level to DEBUG
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define the log message format
                        datefmt='%Y-%m-%d %H:%M:%S',  # Define the date format
                        filename=f'app_parse_tracer.log',  # Log messages to a file named 'app.log'
                        filemode='w')  # Open the log file in write mode
    logger = logging.getLogger(os.path.basename(__file__))

    clean_repos = analyse_files()
    filepath = os.path.join('./results', 'safe_dynamic_model_files.txt')
    with open(filepath, 'w') as f:
        for line in clean_repos:
            f.write(f"{line}\n")
    
    #parse_strace_text()
