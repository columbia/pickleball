# PickleBall

PickleBall protects machine learning engineers when loading untrusted
pickle-based machine learning models.

PickleBall ensures that the when loading an untrusted model, only functions that
are necessary for loading the model are executed. PickleBall infers this allowed
code by analyzing the source code of the machine learning library used to
produce the model.

In order to use PickleBall, the machine learning engineer needs to know the
library that produced the model (often the same as the library used to load the
model) and the Python class of the model once loaded.

PickleBall works in two steps:
1. Policy inference: TODO
2. Policy enforcement: TODO

Policy inference only needs to run once per machine learning library.

# Setup

1. Build the static inference Docker container (`inference container`) with our
Joern fork:

TODO: Submodule the Joern fork into this repository and build directly from
here.

```
$ docker build -t joern .
```

2. Build the base dynamic enforcement Docker container (`enforcement container`):

```
$ cd enforce
$ docker build -t pickleball-enforce -f Dockerfile .
$ docker build -t pickleball-enforce-deb11 -f Dockerfile.deb11 .
```

# Policy Generation

PickleBall uses the Joern program analysis platform to generate policies for
model class objects. The policy need only be generated once for a given class,
and then used anytime a model of that class is loaded.

PickleBall provides a containerized environment to generate model policies with
the following steps:

1. Run the container and mount this directory in the container. If analyzing a
   target that is not in the evaluation dataset, ensure that the target source
   code is also mounted in the counter.

```
$ docker run -it --rm -v $(pwd):/pickle-defense joern /bin/bash
```

2. Use Joern-Parse to create a CPG for the analysis target. For best results,
   you may need to provide the Joern process with maximum system memory
   resources (`-J-Xmx`) and exclude source directories that are unnecessary for
   analysis (e.g., test files).

```
# /joern/joern-cli/target/universal/stage/pysrc2cpg -J-Xmx16g /pickle-defense/evaluation/libraries/flair/flair/ -o /pickle-defense/evaluation/libraries/flair/flair.cpg --ignore-paths="/pickle-defense/evaluation/libraries/flair/flair/tests/,/pickle-defense/evaluation/libraries/flair/flair/examples/,/pickle-defense/evaluation/libraries/flair/flair/flair/datasets"
```

3. Use Joern to execute the `analyze.sc` script. Provide a path to the CPG,
   the name of the class to generate a policy for, (optionally) an output file path
   to write the inferred policy to, and (optionally) a path to the cache
   directory:

```
# /joern/joern --script /pickle-defense/analyze/analyze.sc --param inputPath=/pickle-defense/evaluation/libraries/flair/flair.cpg --param modelClass="flair/models/sequence_tagger_mode.py:<module>.SequenceTagger" --param outputPath=/pickle-defense/evaluation/libraries/flair/models/SequenceTagger/policy.json --param cache=/pickle-defense/evaluation/cache
```

The steps above will produce a policy file named
`flair-sequence-tagger-policy.json` for loading models that implement the
`SequenceTagger` class of the `flair` library.

# Policy Enforcement

PickleBall enforces load policies when loading a model. We provide an
enforcement container for model loading.

Note: the current implementation of PickleBall overwrites the system Pickle
module with our custom version that enforces policies. Therefore, we recommend
using our provided enforcement container image to load models, but it is not
strictly necessary. Future implementations will not overwrite the Pickle module.


# Evaluating PickleBall on a library and model

We evaluate PickleBall on a dataset of models. We identify the libraries used to
produce the model and the class implemented by the model. PickleBall generates a
policy for the class, and then we enforce the policy while loading the model and
performing an intended task (e.g., inference).

Each library is added as a submodule to in the `evaluation/libraries/`
directory. Within each library subdirectory, the `models/` subdirectory contains
all models in the dataset organized by class.

Example for the `flair` library:

`evaluation/libraries/flair`:
- `flair/`: source code of `flair` library for analysis
- `Dockerfile`: Dockerfile to build a version of the `enforce container` with
   flair dependencies installed.
- `infer.sh`: bash script for inferring policies for model classes in the flair
   library. Intended to be executed in the `inference container`.
- `models/SequenceTagger`: subdirectory containing all analysis results for the
   `SequenceTagger` class of the flair library.
   - `policy.json`: policy inferred by the `infer.sh` script
   - `load.py`: program that loads all models in the dataset that load as
      `SequenceTagger` objects and executes an intended task, like inference.
   - `enforce.sh`: bash script for starting the `enforce container` with the
      `policy.json` and `load.py` files mounted appropriately for enforcement.

To add a library to the evaluation dataset:

1. Create a subdirectory for the library in the `evaluation/libraries`
   directory.

2. Add the library as a submodule to the repository.

3. Identify model classes in the library for evaluation, and the models that
   implement the model classes. Create appropriate directories in the `models/`
   subdirectory.

4. Create an `infer.sh` script to infer policies for each model class and place
   the analysis results in the appropriate `models/` subdirectory.

5. For each model class, create a `load.py` script that loads the models that
   implement the class and performs the models' intended functionality.

6. For each model class, create an `enforce.sh` script that starts the
   `enforce container`, mounts the inferred policy, and executes the `load.py`
   script.

If the `load.py` script successfully executes for all model classes in the
evaluation dataset, then we consider the evaluation of the library a success.

# Run inference tests

In the inference docker container:

```
# python3 runtests.py
```

# Tracing a model

Given a pickle-based model, to generate a trace of the imported and invoked
callables in the model:

1. Extract the pickle program from the model. For PyTorch v1.3 models, this
   means unzipping the `pytorch_model.bin` file to access `data.pkl`.

2. Use the fickling module and our scripts to generate a JSON trace of all
   model imports and invocations:

```
$ fickling --trace data.pkl > data.trace
$ python3 scripts/parsetrace.py data.trace > data.json
```

3. (Optional) Given a set of model traces, generate a trace that contains all
   imports and invocations seen in the model traces.
```
$ python3 scripts/modelunion.py `echo <name of model class>` data.json data2.json ... > baseline.json
```

# Troubleshooting

## Joern crash

Non-determinism in Joern may result in a crash on some executions. If one
occurs, first try re-executing Joern. If this occurs while running the inference
test suite, first re-execute the test suite. You can also run individual tests
by providing them as arguments by name with the `--fixtures` option. List all
available tests with the `--list` option.
