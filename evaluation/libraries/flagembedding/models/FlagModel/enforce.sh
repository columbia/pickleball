#!/bin/bash

docker run --rm -it \
    -v $(pwd)/policy.json:/root/policies/policy.json \
    -v $(pwd)/load.py:/load-model/load.py \
    -v /proj/rcs-ssd/phli/pickleball/malicious:/models \
    pickleball-flagembedding /bin/bash
