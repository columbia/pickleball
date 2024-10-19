#!/bin/bash

docker run --rm -it \
    -v $(pwd)/policy.json:/root/policies/policy.json \
    -v $(pwd)/load.py:/load-model/load.py \
    pickleball-flagembedding /bin/bash
