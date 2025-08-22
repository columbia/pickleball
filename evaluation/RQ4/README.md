# RQ4: Comparison to SOTA

## ModelScan

1. Install modelscan with `pip install modelscan==0.8.1`.
2. Run modelscan against both benign and malicious models:

```bash
bash eval-modelscan.sh file-of-model-path
# e.g., bash eval-modelscan.sh malicious-model-on-host.txt
```

## ModelTracer

Since this loads models, run within a container or VM using our provided Docker image:

```bash
bash eval-modeltracer.sh file-of-model-path docker-image timeout
# e.g., bash eval-modeltracer.sh malicious-model-on-host.txt modeltracer:latest 80
```

**Note**: This outputs 43 malicious models while our paper states 44. One model (`mkiani/gpt2-exec/gpt2-exec/pytorch_model.bin`) hangs in interactive mode wth `pdb` but completes non-interactively. For the full 44 count, manually run:

```bash
docker run -it modeltracer:latest /bin/bash
cd /root/modelscan/
python3 -m scripts.model_tracer /path/to/mkiani/gpt2-exec/gpt2-exec/pytorch_model.bin torch
python3 -m scripts.parse_tracer
```

## Weights-only
```bash
python3 eval-weights-only.py file-of-model-path
# e.g., python3 eval-weights-only.py malicious-model-on-host.txt
```