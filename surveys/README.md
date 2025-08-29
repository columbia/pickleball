# Surveys

This directory contains the data and scripts for the surveys on Hugging Face Pickle Models ($3.1).

Here are the steps to reproduce the results:

1. Download the [data.tar.gz](https://drive.google.com/file/d/1SnZrINhQTvQjG0dxIwJ6ZNB80Pp9pHme) file and extract it to the `surveys/data` directory.
2. Run the following commands to generate Figure 2:
```sh
python figure2.py
```

This will generate the longitudinal analysis figure for pickle and safetensors downloads (Figure 2 in the paper).

3. Run the following commands to generate Figure 3:
```sh
python figure3.py
```

This will generate the proportion of model formats and downloads in March 2025 (Figure 3 in the paper).