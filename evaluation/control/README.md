# Control Experiment

The purpose of this directory is to provide resources to ensure:
1. All evaluated libraries APIs can load their associated benign models in our
   dataset; and
2. All evaluated libraries can load a "malicious" model.

(1) is important for ensuring that we are using the loading APIs correctly.
If the loading program, running with the regular Python interpreter and pickle
module, cannot load the model, the we cannot penalize PickleBall for also
failing to load the model.

(2) is important for ensuring that the loading API is vulnerable to malicious
model loading. If the API already prevents malicious models from being loaded,
then it does not need to be protected with PickleBall*.

*However, it may be worthwhile to still include in the dataset to show that
PickleBall does not restrict these models from loading.

## Ensure all models load

To ensure that all models load (1), run the `control-load-all` docker compose
service from the root of the PickleBall project. The results will be placed in
the `evaluation/enforce/results/` directory, and can be converted to a LaTeX
table:

```bash
docker compose run control-load-all
python3 scripts/generatetable evaluation/manifest --enforcement-results evaluation/enforcement/results
```

Expect that all models (100%) are loaded.

## Ensure all libraries are vulnerable

We provide a "malicious" model that uses disallowed (by the PyTorch Weights Only
Unpickler) callables to write a file to the file system. If this model is
successfully loaded and used to write the file, then the library is vulnerable.
