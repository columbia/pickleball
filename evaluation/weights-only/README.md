# Evaluation - Weights-only Unpickler on dataset

## Benign model loading

The weights only unpickler is expected to load all benign models in our 
dataset.

For each set of library models, determine how many are loaded with
`scripts/load_weights_only.py`.

```
python3 scripts/load_weights_only.py /path/to/models/library/ --out evaluation/weights-only/benign/library-weights/only
```

This produces a summary file that indicates the number of models attempted, successfully loaded, and failed.


## Malicious model loading

TODO
