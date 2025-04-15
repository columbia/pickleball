## Tracing a model

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

