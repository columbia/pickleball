#!/bin/bash

docker run --rm -it \
    -v $(pwd)/policy.json:/root/policies.json \
    -v $(pwd)/load.py:/load-model/load.py \
    pickleball-pyannote /bin/bash
