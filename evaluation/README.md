# Evaluation

PickleBall's evaluation (Section 6) addresses four Research Questions with
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

To validate these claims, the steps below demonstrate how to reproduce the data
presented in Table 1, Table 2, Figure 6, and Figure 7 of the PickleBall paper.
By following the steps, you will be able to validate that the outputs match
what is presented in these tables.

These tables and figures support our main claims:
* RQ1 is supported by Table 2 showing that PickleBall has a 0% false negative
  rate.
* RQ2 is supported by Table 1 showing that PickleBall successfully loads 79% of
  benign models.
* RQ3 is supported by Figure 6 and Figure 7 showing PickleBall's policy
  generation time and enforcement overhead.
* RQ4 is supported by Table 2 showing how PickleBall performs in comparison to
  the Weights Only Unpickler, ModelScanner, and ModelTracer.

Prior to reproducing the evaluation, you should familiarize yourself with the
PickleBall implementation as described in the top level README.

## Preparation

The following steps assume that you will evaluate using the full benign model
dataset (130GB compressed). We also provide an abridged dataset (10GB
compressed) if you wish to evaluate but not completely reproduce all results.
If you choose to use the abridged dataset, follow the steps below but update
them where noted.

1. Create a directories outside of this repository to host the model datasets.
For example, if you choose to use your home directory, run the following commands:

```
$ mkdir -p ~/models/benign
$ mkdir -p ~/models/malicious

# Optional
$ mkdir -p ~/models/benign-abridged
```

2. Download and extract the model dataset archives and place them in their respective directories.

Download URLs:
* benign models: https://zenodo.org/records/16974645/files/benign.tar.gz?download=1
* malicious models: https://zenodo.org/records/16891393/files/malicious.tar.gz?download=1
* benign-abridged models: https://zenodo.org/records/16891393/files/benign-abridged.tar.gz?download=1

Note that the archives decompress into the directory that they are placed in;
they do not create a new subdirectory.

Downloading and decompressing all 140GB of data may take ~1 hour depending on
network speeds.

```
$ cd ~/models/benign
$ wget https://zenodo.org/records/16974645/files/benign.tar.gz?download=1
$ tar xzvf benign.tar.gz
$ cd ~/models/malicious
$ wget https://zenodo.org/records/16891393/files/malicious.tar.gz?download=1
$ tar xzvf malicious.tar.gz

# Optional
$ cd ~/models/benign-abridged
$ wget https://zenodo.org/records/16891393/files/benign-abridged.tar.gz?download=1
$ tar xzvf benign-abridged.tar.gzz
$ mv models-list-abdridged.txt models-list.txt
```

**Note:** if you use the benign-abridged models, please ensure that you rename the
`models-list-abridged.txt` file to `models-list.txt`.

3. In the PickleBall repository root, create a `.env` file that sets the following 
environment variables:

```
BENIGN_MODELS=<path to benign models directory (e.g., ~/models/benign)>
MALICIOUS_MODELS=<path to malicious models (e.g., ~/models/malicious)>
```

If you choose to evaluate on the abridged models, change the `BENIGN_MODELS`
value to point to the `benign-abridged` directory.

4. Build all docker containers.

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

**Note:** unless otherwise indicated, all following commands should be executed
from the `evaluation/` directory.

## RQ1 & RQ2 - PickleBall policies block malicious models and load benign models

To validate RQ1 and RQ2, the following steps will reproduce Table 1 and the
last row of Table 2.

### 1. Generate policies for all libraries in the PickleBall evaluation dataset.

**Command** (approximately 10 minutes to execute):

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

**Command** (approximately 20 minutes to execute):

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

**Command** (immediate):

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

**Command** (approximately 20 minutes to execute):

```
$ docker compose run weightsonly-load-all
```

**Expected result**:
* `evaluation/weights-only/results-benign/<library>.log`: analogous to Step 2
  above for enforcing PickleBall policies, this step produces log files
  indicating whether the Weights-Only Unpickler default policy successfully
  loads the library's models.

### 5. Analyze results and compare to Table 1

**Command** (immediate):

```
$ python3 ../scripts/generatetable.py manifest.toml weights-only/results-benign
```

**Expected results**:

This outputs the same LaTeX table as before, but this time the last column should
match the WOUp column in Table 1, indicating number of models that the
Weights-Only Unpickler successfully loaded.

This concludes the reproduction of Table 1 of our results.

### 6. Enforce policies while loading malicious models

**Note:** this step will attempt to load malicious models. The `RQ1-blocking.sh`
script will start a docker container, and all models will be loaded in the
container. If additional protection is desired, you may create a virtual machine.

**Command** (approximately 10 minutes):

```sh
$ ./RQ1-blocking.sh
```

**Expected results**:

* `evaluation/enforcement/results-malicious/malicious-<library>.log` file created
  for each library. Each file indicates the number of malicious models that were
  successfully loaded when loaded with PickleBall's policy for that library.
  Manual inspection of each file should show that no malicious models are
  successfully loaded (last line of each file should indicate `0:84`).

**Explanation**:

The `RQ1-blocking.sh` script invokes each library container with the appropriate
PickleBall policy loaded for the library, and attempts to load each of the 84
malicious models in our dataset. The `enforcement/load_all.py` script is invoked to perform
the model loading, which in turn invokes `enforcement/loadmalicious.py`.

## RQ3: Performance

To validate claims about PickleBall's performance, the steps below reproduce
data used to create Figure 6 and Figure 7.

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

## RQ4: Comparison to SOTA

To validate RQ4, following steps indicate how to execute the compared
state-of-the-art tools on the PickleBall model datasets, replicating rows 1-3 of
Table 2 (row 4 was already replicating in RQ1 and RQ2).

### ModelScan

This step runs [ModelScan](https://github.com/protectai/modelscan/tree/v0.8.1)
against both malicious and benign models. The following command starts a
container using the `modelscan:latest` Docker image built earlier and tests each
model.

**Command** (approximately 20 minutes):

```bash
$ docker compose run modelscan
```

**Expected results**:

This command will show the analysis progress and results of individual models on the terminal and finally output the results corresponding to the first row in Table 2.
```
Tool        #TP     #TN     #FP     #FN     FPR     FNR
ModelScan   75      236     16      9       6.3%    10.7%
```

### ModelTracer

This step runs
[ModelTracer](https://github.com/s2e-lab/hf-model-analyzer/tree/5725b26f62a1c0e4f22c793761cefb70ead64ee5)
against both malicious and benign models. The following command starts a
container per model using the `modeltracer:latest` Docker image built earlier
and tests it.

**Note:** this step **will load** malicious models. The `RQ4-modeltracer.sh`
script will start a docker container, and all models will be loaded in the
container. If additional protection is desired, you may create a virtual
machine, and the models will execute their payloads. The payloads will not
alter system state outside of the container, but you may wish to temporarily
disable network connectivity. The ModelTracer tool that we compare to must
execute the model in order to trace its behavior.

**Command** (approximately 75 minutes):

```bash
$ ./RQ4-modeltracer.sh
```

**Expected results**:

Similarly, this command will show the analysis progress and results of individual models on the terminal and finally output results like the following:
```
Tool        #TP     #TN     #FP     #FN     FPR     FNR
ModelTracer 43      252     0       41      0%      48.8%
```

**Note**:

Compared to the second row of Table 2, the above shows 43 TP detections instead of 44. This is because one model hangs in interactive mode and should be manually verified. The steps to verify this are as follows:

```sh
$ docker run -dit --name modeltracer_container modeltracer:latest
$ docker cp $MALICIOUS_MODEL/mkiani/gpt2-exec/gpt2-exec/pytorch_model.bin modeltracer_container:/root/modeltracer/pytorch_model.bin
$ docker exec -it modeltracer_container /bin/sh

# in the container, run:
$ python3 -m scripts.model_tracer /root/modeltracer/pytorch_model.bin torch
$ python3 -m scripts.parse_tracer
```

### Weights-Only Unpickler

This step runs the weights-only unpickler against both malicious and benign
models. The following command starts a container using the `weightsonly:latest`
Docker image and tests each model.

**Command** (approximately 5 minutes):

```sh
$ docker compose run weightsonly
```

**Expected Results**:

This produces the third row of Table 2:
```
Tool        #TP     #TN     #FP     #FN     FPR     FNR
WeightsOnly 84      157     95      0       37.7%   0.0%
```

### PickleBall

The results are already obtained and explained in RQ1 and RQ2, which are copied
into row 4 of Table 2.
