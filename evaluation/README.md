# Evaluation

PickleBall's evaluation (Section 6) addresses four Research Questions and makes
the following claims:

* RQ1: PickleBall generates policies that blocks all malicious models from
  loading.
* RQ2: PickleBall generates policies that loads 79% of benign models.
* RQ3: PickleBall generates policies in a reasonable amount of time, and it
  enforces policies with minimal overhead.
* RQ4: PickleBall compares favorably to other state of the art tools.

This README provides steps to reproduce these claims. These steps assume that
you have access to this code repository and the malicious and benign models
distributed in the PickleBall artifact.

The steps below demonstrate how to reproduce the data provided in Table 1,
Table 2, Figure 6, and Figure 7 of the PickleBall paper.

TODO: map the tables and figures to the RQs being addressed.

Prior to reproducing the evaluation, you should familiarize yourself with the
PickleBall implementation as described in the top level README.

## Preparation

Download all models the evaluation dataset from the following locations:
- Benign models: TODO
- Malicious models: TODO

Decompress each at a location outside of this code repository.

1. Create a `.env` file in the repository root (i.e., `../.env`) that sets the
following environment variables:

```
BENIGN_MODELS=<path to benign models>
MALICIOUS_MODELS=<path to malicious models>
```

2. Build all docker containers.

From the repository root:

```
$ docker compose build
```

This will take approximately TODO minutes.

This builds the following relevant container images (specified in the
`../docker-compose.yml` file):
* `pickleball-generate`: Container image with the PickleBall policy generator
  installed. Used to analyze library source code and generate policies. Includes
  the Joern program analysis tool and our modifications (`analyze/joern.diff`).
* `pickleball-enforce`: Container image with the PickleBall loader installed in a
  Debian 12 environment. Used to load models. We use this container image as the
  base image when installing library-specific dependencies for each library.
* `pickleball-enforce-deb11`: Container image with the PickleBall loader
  installed in a Debian 11 environment. Used to load models. We use this
  container image as the base image when installing library-specific
  dependencies for each library, when the Debian 12 environment is incompatible.

## Reproduce Policy Generation Table (Table 1)

Table 1 shows that when PickleBall generates policies for each library in the
dataset, ... TODO

### 1. Generate policies for all libraries in the PickleBall evaluation dataset.

**Command** (from repository root), approximately 10 minutes to execute:

```
$ docker compose run generate-all
```

**Expected result:**
* `evaluation/policies/<library>.json` file is created for each library in the
  evaluation dataset. These files are the policies that PickleBall generates
  after analyzing the library source code.
* `results/<timestamp>.timelog` file containing the elapsed time in seconds to generate each policy for each library.

**Explanation:**

This command invokes the following actions inside the policy generation
container:
1. Executes `evaluation/setup/fetch.sh` to fetch all evaluation libraries
  and apply our manual modifications, which can be inspected in
  `evaluation/setup/*.diff` files (described in Section 6.1 "Library Preprocessing").
2. Executes `evaluation/generate-policies.py` to analyzes and generates policies
  for each library. This script is configured based on the
  `evaluation/manifest.toml` file, which specifies how the `pickleball-generate`
  program is invoked for each library in the evaluation dataset.

**Note:** For two libraries (parrot, TNER), a non-deterministic bug in Joern may
result in a crash. The `generate-policies.py` program will attempt to retry the
analysis for these libraries until it succeeds. We notice higher chance of
success when run on smaller hardware (e.g., laptop with 12 cores and 32GB RAM)
than on larger (e.g., server with 128 cores and 256GB RAM).

### 2. Enforce policies while attempting to load all benign models in the dataset

**Command** (from `evaluate/` directory), approximately 20 minutes to execute:

```
$ ./enforce-all.sh
```

**Expected result:**
* `evaluation/enforce/results/<library>.log` file is created for each library
  in the evaluation dataset. These files record the outcome of attempting to
  load each model in the dataset with its corresponding library API, while
  PickleBall enforces the generate policy for the library.

**Explanation:**

This command starts one container for each library in the dataset. The container
has the library and its dependencies installed, as well as the PickleBall loader
and the generated policy for the library (the container images are defined in
`evaluation/enforcement/Dockerfile.<library>`).

In each library container, the `evaluation/enforcement/load_all.py` script
attempts to load each model associated with the library from the benign models
dataset.

The output `<library>.log` file records whether each model was loaded
successfully or not. The last line of each log file is in the format `X:Y` where
`X` represents the number of models successfully loaded, and `Y` represents
the total number of models attempted.

### 3. Analyze results and compare to Table 1

**Command**:

```
$ python3 ../scripts/generatetable.py manifest.toml enforcement/results
```

**Expected result**:

This outputs a LaTeX table (that can optionally be compiled with pdflatex, or
compared directly) and compared to Table 1. The final column ought to match the
final column of Table 1, indicating the number of models that PickleBall
successfully loads.

The values in the `imports` and `invocations` sections of the table are produced
by comparing the callables in the generated policies (`evaluation/policies/*.json`)
to the callables that are observed in the models in the benign dataset, which
we manually trace and record (`evaluation/policies/baseline/*.json`).

Note that the generated table does not contain the results from the Weights-Only
Unpickler (WOUp column in Table 1), which we will collect and analyze next.

### 4. Enforce Weights Only Unpickler policies while attempting to load all benign models in the dataset

**Command**:

```
$ docker compose run weightsonly-load-all
```

**Expected result**:
* `evaluation/weights-only/results-benign/<library>.log`: analogously to when
  enforcing PickleBall policies, this step produces log files indicating whether
  the Weights-Only Unpickler default policy successfully loads the library's
  models.

### 5. Analyze results and compare to Table 1

**Command**:

```
$ python3 ../scripts/generatetable.py manifest.toml weights-only/results-benign
```

**Expected results**:

This outputs the same LaTeX table as before, but this time the last column should
match the WOUp column in Table 1, indicating number of models that the
Weights-Only Unpickler successfully loaded.

This concludes the reproduction of Table 1 of our results.

## RQ1: Malicious Model Blocking
Similar to loading benign models, this script starts a container with each library's Pickleball policy and attempts to load malicious models.

```sh
$ ./RQ1-blocking.sh
```

The command will show the enforcement results for each library on the terminal and output all malicious models are blocked.

## RQ4: Comparison to SOTA

### ModelScan (20 mins)
This step runs [ModelScan](https://github.com/protectai/modelscan/tree/v0.8.1) against both malicious and benign models. The following command starts a container using the `modelscan:latest` Docker image built earlier and tests each model.

```bash
$ docker compose run modelscan
```

This command will show the analysis progress and results of individual models on the terminal and finally output the results corresponding to the first row in Table 2.
```
Tool        #TP     #TN     #FP     #FN     FPR     FNR
ModelScan   75      236     16      9       6.3%    10.7%
```

### ModelTracer (75 mins)
This step runs [ModelTracer](https://github.com/s2e-lab/hf-model-analyzer/tree/5725b26f62a1c0e4f22c793761cefb70ead64ee5) against both malicious and benign models. The following command starts a container per model using the `modeltracer:latest` Docker image built earlier and tests it.

```bash
$ ./RQ4-modeltracer.sh
```

Similarly, this command will show the analysis progress and results of individual models on the terminal and finally output results like the following:
```
Tool        #TP     #TN     #FP     #FN     FPR     FNR
ModelTracer 43      252     0       41      0%      48.8%
```

Compared to the second row of Table 2, the above shows 43 TP detections instead of 44. This is because one model hangs in interactive mode and should be manually verified. The steps to verify this are as follows:
```sh
$ docker run -dit --name modeltracer_container modeltracer:latest
$ docker cp $MALICIOUS_MODEL/mkiani/gpt2-exec/gpt2-exec/pytorch_model.bin modeltracer_container:/root/modeltracer/pytorch_model.bin
$ docker exec -it modeltracer_container /bin/sh

# in the container, run:
$ python3 -m scripts.model_tracer /root/modeltracer/pytorch_model.bin torch
$ python3 -m scripts.parse_tracer
```

### Weights-Only (5 mins)
This step runs the weights-only unpickler against both malicious and benign models. The following command starts a container using the `weightsonly:latest` Docker image and tests each model.

```sh
$ docker compose run weightsonly
```

This produces the third row of Table 2:
```
Tool        #TP     #TN     #FP     #FN     FPR     FNR
WeightsOnly 84      157     95      0       37.7%   0.0%
```

TODO: add explanation - this also loads malicious models (in addition to the
benign ones from Table 1)

TODO: add analysis - Row X in Table 2

### PickleBall

The results are already obtained and explained in RQ1 and RQ2.

TODO: the final row in Table 2 is reproduced from results already checked above.

## Performance

### Figure 6 - Policy Generation Runtime

The policy generation should have produced a file under
`results/<timestamp>.timelog` containing the time to generate the policy for
each library, corresponding to Figure 6. The results can be pretty-printed as a
table by running

```
python3 scripts/analyze_generation_times.py
```

In our experiment setup (14-core Intel i7 CPU and 32GB of RAM), the policy
generation required anywhere ~10 to ~30 seconds depending on the library. The
exact numbers may vary due to noise or different setups, but you should expect
to see generation times in a similar range.

### Figure 7 - Policy Enforcement Runtime Overhead

Load time performance experiment (approximately 5 minutes):

```
$ mkdir results
$ scripts/run-load-time.sh
$ python3 scripts/analyze_load_times.py
```

This will produce a table showing the load time overheads of the PickleBall
loader. To rerun this experiment, delete the file at `results/times.csv` and
rerun the above scripts.

This experiment can be noisy and load times for the same model may vary between
runs. To counteract this, our script first loads each model 3 times without
measuring the load times to ensure it has been loaded in memory, then measures
the load time for 10 more loads, and finally presents the average load time
after removing outliers. This reduces the fluctuation due to noise but does not
completely eliminate it, so the overhead of the PickleBall loader may vary
across runs and may even have negative overhead (i.e., speedup) for some models.
However, you should still see a similar pattern: the overhead of using the
PickleBall loader should be relatively small.
