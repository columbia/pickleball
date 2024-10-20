#!/bin/bash

docker run --rm -it \
    -v $(pwd)/policy.json:/root/policies/policy.json \
    -v $(pwd)/load.py:/load-model/load.py \
    -v $(pwd)/ko-sroberta-multitask/:/load-model/ko-sroberta-multitask/ \
    pickleball-sentencetransformers /bin/bash
