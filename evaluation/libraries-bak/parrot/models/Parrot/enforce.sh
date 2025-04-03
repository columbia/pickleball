#!/bin/bash

docker run --rm -it \
    -v $(pwd)/policy.json:/root/policies/policy.json \
    -v $(pwd)/load.py:/load-model/load.py \
    -v $(pwd)/try_all.py:/load-model/try_all.py \
    -v ~/data/malicious/:/models \
    pickleball-parrot /bin/bash
