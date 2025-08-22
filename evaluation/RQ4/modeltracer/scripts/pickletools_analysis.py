import os
import pickletools
import zipfile
import sys



def check_safety(model_file, outfile):
    """
    This function is used to check the safety of a file before loading it.
    """
    with open(model_file, "rb") as f:
            data = f.read()

    final_out = './results' / outfile

    with open(final_out, 'w') as f:
        pickletools.dis(data,out=f)


def begin_analysis(model_file, outfile):
    try:
        with zipfile.ZipFile(model_file, 'r') as f:
                # make path within current directory to extract. we will have to delete in the end so we dont iterate through it for the
                # rest of analysis
                #model_filename = 
                unzippedFolder = './unzippedFiles/'
                root_path = os.path.dirname(model_file)
                unzippedPath = os.path.join(root_path, *unzippedFolder.split("/"))
                f.extractall(path=unzippedPath)
                # getting all files in the zip file
                files = os.listdir(unzippedPath)
                for file in files:
                    full_file_path = os.path.join(unzippedPath, *file.split("/"))
                    if os.path.isdir(full_file_path):
                        for i in os.listdir(full_file_path):
                            if i == 'data.pkl':
                                full_pkl_path = os.path.join(full_file_path, *i.split("/"))
                                check_safety(full_pkl_path, outfile)
    except:
        pass


if __name__ == '__main__':
    # Delete the folder where the models are being cloned upon program exit
   

    # check if the user provided the start and end index
    if len(sys.argv) != 3:
        print("Please provide the path to the model file and the desired name for the outfile as a txt.")
        sys.exit(1)
    # get start index and end index from the command line
    model_file = sys.argv[1]
    outfile = sys.argv[2]

    begin_analysis(model_file, outfile)