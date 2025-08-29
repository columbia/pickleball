# Surveys

This directory contains the data and scripts for the surveys on Hugging Face Pickle Models ($3.1).

Here are the steps to reproduce the results:

1. Download the [data.tar.gz](https://drive.google.com/file/d/1SnZrINhQTvQjG0dxIwJ6ZNB80Pp9pHme) file and extract it to the `surveys/data` directory.
The data is a collection of longitudinal data from multiple resources, including:
  - [**PTMTorrent**](https://github.com/SoftwareSystemsLaboratory/PTMTorrent): We directly take the metadata (`PTMTorrent.json`) from the PTMTorrent dataset.
  - [**HFCommunity**](https://som-research.github.io/HFCommunity/): We use the [script](./data/hfcommunity_downloads.py) to download the dataset checkpoints collected from *May 2023* to *Octorber 2023*
  - Multiple checkpoints from an internal database from [**Socket**](https://socket.dev/) which were collected using `huggingface_hub` API. This includes data from *August 2024*, *November 2024*, and *March 2025*.

  This covers the longitudinal data from *January 2023* to *March 2025*. We filtered models with over 1000 monthly downloads from each database, and extracted the `siblings` metadata, which includes all the files in each model repository. We provide the extracted data to support the reproducibility of our survey study ($3).

   
3. Run the following commands to generate Figure 2:
```sh
python figure2.py
```

This will generate the longitudinal analysis figure for pickle and safetensors downloads (Figure 2 in the paper).

3. Run the following commands to generate Figure 3:
```sh
python figure3.py
```

This will generate the proportion of model formats and downloads in March 2025 (Figure 3 in the paper).
