#!/bin/bash

docker run --rm -it \
    -v $(pwd)/policy.json:/root/policies/policy.json \
    -v $(pwd)/load.py:/load-model/load.py \
    -v $(pwd)/try_all.py:/load-model/try_all.py \
    -v $(pwd)/ko-sroberta-multitask/:/load-model/ko-sroberta-multitask/ \
    -v ~/data/no-malicious/sentence-transformers/SequenceTransformer:/models \
    pickleball-sentencetransformers /bin/bash
