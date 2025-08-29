#!/bin/bash

docker compose run enforce-conch /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-flagembedding /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-flair /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-gliner /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-huggingsound /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-languagebind /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-melotts /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-parrot /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-pyannote /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-pysentimiento /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-sentencetransformers /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-superimage /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-tner /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-tweetnlp /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-yolov5 /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious && \
docker compose run enforce-yolov11 /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious
