# Surveys

## Pickle prevalence survey

This directory contains the data and scripts for the surveys on Hugging Face
Pickle Models ($3.1).

Here are the steps to reproduce the results:

TODO: validate download link.

1. Download the
   [data.tar.gz](https://zenodo.org/records/16891393/files/data.tar.gz?download=1&preview=1)
   file to the `surveys/` directory and extract it (`tar xzvf data.tar.gz`) to
   create the `surveys/data/` directory.

The data is a collection of longitudinal data from multiple resources, including:
  - [**PTMTorrent**](https://github.com/SoftwareSystemsLaboratory/PTMTorrent):
    We directly take the metadata (`PTMTorrent.json`) from the PTMTorrent
    dataset.
  - [**HFCommunity**](https://som-research.github.io/HFCommunity/): We use the
    [script](./hfcommunity_downloads.py) to download the dataset
    checkpoints collected from *May 2023* to *October 2023*
  - Multiple checkpoints from an internal database from
    [**Socket**](https://socket.dev/) which were collected using
    `huggingface_hub` API. This includes data from *August 2024*, *November 2024*,
    and *March 2025*.

This covers the longitudinal data from *January 2023* to *March 2025*. We
filtered models with over 1000 monthly downloads from each database, and
extracted the `siblings` metadata, which includes all the files in each model
repository. We provide the extracted data to support the reproducibility of our
survey study ($3).

2. Run the following commands to generate Figure 2:
```sh
python figure2.py
```

This will generate the longitudinal analysis figure for pickle and safetensors
downloads (Figure 2 in the paper).

3. Run the following commands to generate Figure 3:
```sh
python figure3.py
```

This will generate the proportion of model formats and downloads in March 2025
(Figure 3 in the paper).

## Pickle Imports Survey

In Section 3.2 we present results showing that many of the pickle models include
imports that are disallowed by the Weights Only Unpickler.

To reproduce this result, run:

```
$ ../scripts/process_csv.py traced_models.csv
```

`traced_models.csv` is a processed file containing imports and metadata of
models we traced during this survey.

It was created with the `../scripts/download_model.py` script, which downloads
models from Hugging Face, traces their imports, and deletes the model (to save
disk space) leaving only the trace file. The output traces were collected into
a single CSV file using the `analyze_traces.py` script, to output the
`traced_models.csv` file above.

Reproducing the study in full can take up to a week and may produce different
results as the model ecosystem changes, so we provide the original processed
CSV.
