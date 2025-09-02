# PickleBall

PickleBall protects users from backdoored pickle-based machine learning models.
The pickle format permits **dangerous arbitrary function calls**, which
attackers abuse by invoking malicious payloads when the model is loaded.
PickleBall ensures that when a model is loaded, it may only call functions
necessary for loading.

PickleBall infers the necessary functions by analyzing the source code of the
machine learning library used to create and load the model. PickleBall enforces
the policy by replacing the pickle module during model loading.

For more details see our paper
[PickleBall: Secure Deserialization of Pickle-based Machine Learning Models](https://www.arxiv.org/abs/2508.15987),
appearing in the proceedings of ACM CCS '25.

## Note to Artifact Evaluators

This top-level README provides general instructions for how to use PickleBall.
To specifically reproduce the results of the PickleBall paper, see:

* `evaluation/README.md`: instructions for reproducing the PickleBall evaluation
  (Section 6 of paper)
* `surveys/README.md`: instructions for reproducing the survey of the Hugging
  Face ecosystem (Section 3.1 and 3.2 of paper)

Our full artifact, including datasets, is hosted on Zenodo at
[https://zenodo.org/records/16974645](https://zenodo.org/records/16974645).

## Overview

PickleBall is composed of two parts:
1. Policy Generator
2. Policy Enforcer

The Policy Generator receives (1) the source code of an ML library and (2) the
class definition in the library to analyze. It outputs a policy for safely
loading the class.

The Policy Enforcer replaces the `pickle` module on the system. It receives (1)
an ML model and (2) the loading policy. It loads the model while enforcing the
given policy.

### Policy Generator

The Policy Generator is executed before loading any models.
`pickleball-generate.py` begins the analysis by collecting user arguments and
invoking the main analysis script, `analyze/analyze.sc`, which performs
PickleBall's analysis and outputs a policy as a JSON file.

### Policy Enforcer

The Policy Executor is executed during model loading. It is implemented in the
`enforce/enforce.py`, which is a modified version of the Pickle Machine and
serves as a drop-in replacement. We provide Dockerfiles (`enforce/Dockerfile`)
for configuring an environment to use the module, where the pickle module is
replaced by the `enforce/enforce.py` module. (Note: in a future re-engineering,
we ought to hook the pickle module rather than replace it entirely.)

## Usage

### Generating Policies

To use PickleBall, we recommended using the `pickleball-generate` docker
container which installs all dependencies for analysis. PickleBall depends on a
custom fork of the Joern static analysis framework, which is installed in the
container.

Build and start the `pickleball-generate` container:

```
$ docker compose run pickleball-generate
```

To analyze a library's source code, you may optionally mount the library source
code in the container when the container starts. This makes the source code
accessible to PickleBall for analysis inside the container:

```
$ docker compose --volume <path-to-library>:/target pickleball-generate
```

You can now execute the `pickleball-generate.py` script inside the container:

```
# cd /pickleball
# ./pickleball-generate.py --help
usage: pickleball-generate.py [-h] --library-path LIBRARY_PATH --model-class MODEL_CLASS [--joern-path JOERN_PATH] [--policy-path POLICY_PATH] [--ignore-paths IGNORE_PATHS] [--cache-path CACHE_PATH] [--use-cpg] [--dry-run]
                              [--mem MEM] [--only-cpg]

Generate a model loading policy for a ML library model class

options:
  -h, --help            show this help message and exit
  --library-path LIBRARY_PATH
                        Path to the ML library source code directory
  --model-class MODEL_CLASS
                        Model class name
  --joern-path JOERN_PATH
                        Path to the joern directory
  --policy-path POLICY_PATH
                        Output policy path
  --ignore-paths IGNORE_PATHS
                        Paths in the ML library to ignore during analysis (e.g., tests directories)
  --cache-path CACHE_PATH
                        Path to cache directory
  --use-cpg             Enable CPG mode (enhanced over AST). Note: this may introduce instability in Joern analysis
  --dry-run             Dry run without executing the Joern utility
  --mem MEM             Maximum amount of system RAM (in GB) to use. If not provided, defaults to using all available memory.
  --only-cpg            Only create CPG and return (without also generating policy)
```

To analyze the library and create a policy, you must provide a path to the
library source code and the name of the model class, as well as the path to the
Joern installation on your system (`/joern` inside the provided container).

#### Model Class Name

PickleBall takes the model class name in Joern's fully-qualified format.

For example, to analyze a class definition `library.module.Class`, Joern
represents this in the form `library/module.py:<module>.Class`. See the
`evaluation/manifest.toml` file for examples of converting Python class names
to the Joern format.

In the future, we aim to support this conversion automatically.

#### Cache

PickleBall can be enhanced with pre-created policies so that when a class with
an existing policy is identified during analysis, PickleBall includes the cached
policy in its analysis.

It is recommended to use PickleBall with the existing pre-computed Weights-Only
Unpickler policy due to the prevalence of PyTorch-based classes. An example of
a cache is provided in the `evaluation/cache` directory. It is recommended that
you run PickleBall with the `--cache-path evaluation/cache` parameter set.

#### CPG vs AST

PickleBall can use Joern to create an Abstract Syntax Tree (AST) or a more
complex Code Property Graph (CPG) which has more recovered type information.
Generally, the CPG produces more accurate results. Use the `--use-cpg` parameter
to indicate whether a full CPG should be created, or just an AST.

Warning: using the full CPG may result in the appearance of a non-deterministc
crash when running Joern. Until the fix is resolved in Joern, we recommend using
the AST mode for stability unless the additional type recovery is necessary
for analysis.

### Policy Format

PickleBall outputs policies in the JSON format. They represent (1) allowed
imports and (2) allowed invocations needed to load a model produced by the
library.

### Enforcing Policies

To use PickleBall to enforce a policy, we provide docker container images with
the PickleBall enforcer pre-installed in place of the regular pickle module.
It is recommended that you create a new Docker container image that is based
from one of the `pickleball-enforce` or `pickleball-enforce-deb11` images, and
install the library and any dependencies needed.

The PickleBall enforcer expects the policy to be located at
`/root/policies/policy.json` inside the container. This can be mounted as a
volume when the container starts with the `--volume` parameter.

Inside the container, ensure that the ML model is accessible. Execute the
program used to load the model, and the PickleBall enforcer will automatically
enforce the provided policy during loading.

For examples of creating a container image, see the `evaluation/enforcement/Dockerfile.<library>` examples.

## Troubleshooting

### Joern crash

Non-determinism in Joern may result in a crash on some executions, typically
appearing as a null dereference. If one occurs, first try re-executing Joern.