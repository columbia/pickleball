# RQ4: Comparison to SOTA

## ModelScan Evaluation
### Setup
```bash
pip install modelscan==0.8.1
```

### Malicious Models (4 minutes)
**Command:**
```bash
sh eval-modelscan.sh malicious-model-on-host.txt
```

**Expected Output:**
```
=== SUMMARY ===
Total model tested: 84
Benign: 9
Malicious: 75

PERCENTAGES:
Benign: 10.7%
Malicious: 89.3%
```

### Benign Models (14 minutes)
**Command:**
```bash
sh eval-modelscan.sh benign-model-on-host.txt
```

**Expected Output:**
```
=== SUMMARY ===
Total model tested: 252
Benign: 236
Malicious: 16

PERCENTAGES:
Benign: 93.7%
Malicious: 6.3%
```


## ModelTracer Evaluation

**WARNING**: ModelTracer dynamically loads models. Use container/VM only.

### Setup
**Command:**
```bash
docker build -t modeltracer:latest .
```

### Malicious Models (25 minutes)
**Command:**
```bash
sh eval-modeltracer.sh malicious-model-on-host.txt modeltracer:latest 80
```

**Expected Output:**
```
=== SUMMARY ===
Total model tested: 84
Unsafe: 43
Safe: 41

PERCENTAGES:
Unsafe: 51% (43/84 models)
Safe: 48% (41/84 models)
```

### Manual Verification for Complete Count
**Note**: The above shows 43 detections. Paper reports 44. One model hangs in interactive mode.

**Commands:**
```bash
docker run -dit --name modeltracer_container modeltracer:latest
docker cp /path/to/mkiani/gpt2-exec/gpt2-exec/pytorch_model.bin modeltracer_container:/root/modeltracer/pytorch_model.bin
docker exec -it modeltracer_container /bin/sh
python3 -m scripts.model_tracer /root/modeltracer/pytorch_model.bin torch
python3 -m scripts.parse_tracer
```

### Benign Models (50 mins)
**Command:**
```bash
sh eval-modeltracer.sh benign-model-on-host.txt modeltracer:latest 80
```

**Expected Output:**
```
=== SUMMARY ===
Total model tested: 252
Unsafe: 0
Safe: 252

PERCENTAGES:
Unsafe: 0% (0/252 models)
Safe: 100% (252/252 models)
```


## Weights-Only Evaluation

### Malicious Models (1 minute)
**Command:**
```bash
python3 eval-weights-only.py malicious-model-on-host.txt
```

**Expected Output:**
```
=== FINAL SUMMARY ===
Total model tested: 84
Loaded: 0
Blocked: 84

PERCENTAGES:
Loaded: 0.0%
Blocked: 100.0%
```

### Benign Models (4 minutes)
**Command:**
```bash
python3 eval-weights-only.py benign-model-on-host.txt
```

**Expected Output:**
```
=== FINAL SUMMARY ===
Total model tested: 252
Loaded: 157
Blocked: 95

PERCENTAGES:
Loaded: 62.3%
Blocked: 37.7%
```
