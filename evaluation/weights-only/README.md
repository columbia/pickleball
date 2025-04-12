# Evaluation - Weights-only Unpickler on dataset

## Benign model loading

In the project root directory, execute: 

```
$ docker compose run weightsonly-load-all
```

This will execute all of the model loaders, but force the weights only 
unpickler to be used.

They will attempt to load all benign models in our dataset.

The results files will be placed in `evaluation/weights-only/results-benign`.

Use the table generating script to display the results (ignore the columns about
PickleBall policy generation and focus only on the model load percentages).

```
$ python3 scripts/generatetable.py evaluation/manifest.toml evaluation/weights-only/benign-results
```

## Malicious model loading

Manual.

TODO: Automate
