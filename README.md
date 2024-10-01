# Model Static Inference

Usage:

1. Build the Docker container with our Joern fork:

```
$ docker build -t joern .
```

2. Run the container and mount this directory in the container (ensure that the
   analysis target is mounted too):

```
docker run -it --rm -v $(pwd):/pickle-defense joern /bin/bash
```

3. Create a CPG for the analysis target:

```
# /joern/joern-parse /pickle-defense/analyze/tests/no-inheritance -o /pickle-defense/analyze/tests/no-inheritance.cpg
```

4. Execute `analyze.sc` script with a path to the CPG and the name of the
   class to infer a policy for:

```
# /joern/joern --script /pickle-defense/analyze/analyze.sc --param inputPath=/pickle-defense/analyze/tests/no-inheritance.cpg --param modelClass=Model --param outputPath=/pickle-defense/analyze/tests/simple-inheritance/models/SpecializedModel/inferred.json
```

The script should output an overapproximate policy:

```
Allowed Globals:
- model.py:<module>.Foo.<returnValue>
- model.py:<module>.Foo.__init__.<returnValue>
- Tensor
- model.py:<module>.Optimizer.__init__
- model.py:<module>.Tensor.__reduce__
- model.py:<module>.Model.__init__
- Optimizer
- Model
- model.py:<module>.Tensor.__init__
Allowed Reduces:
- model.py:<module>.create_tensor
```

## Run tests

In the docker container:

```
# python3 runtests.py
```

Non-determinism in Joern may result in a crash - if one occurs, first try
re-running the test suite. You can also run individual tests by providing them
as arguments by name with the `--fixtures` option. List all available tests
with the `--list` option.
