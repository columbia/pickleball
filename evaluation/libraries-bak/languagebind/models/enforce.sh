#!/bin/bash

docker run --rm -it \
    -v $(pwd)/policy.json:/root/policies/policy.json \
    -v $(pwd)/load.py:/LanguageBind/load.py \
    -v $(pwd)/LanguageBind_Video_FT:/load-model/LanguageBind_Video_FT \
    pickleball-languagebind /bin/bash
