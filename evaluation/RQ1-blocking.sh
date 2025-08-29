#!/bin/bash

docker compose run enforce-conch /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library conch --test-malicious && \
docker compose run enforce-flagembedding /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library flagembedding --test-malicious && \
docker compose run enforce-flair /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library flair --test-malicious && \
docker compose run enforce-gliner /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library gliner --test-malicious && \
docker compose run enforce-huggingsound /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library huggingsound --test-malicious && \
docker compose run enforce-languagebind /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library languagebind --test-malicious && \
docker compose run enforce-melotts /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library melotts --test-malicious && \
docker compose run enforce-parrot /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library parrot --test-malicious && \
docker compose run enforce-pyannote /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library pyannote --test-malicious && \
docker compose run enforce-pysentimiento /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library pysentimiento --test-malicious && \
docker compose run enforce-sentencetransformers /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library sentencetransformers --test-malicious && \
docker compose run enforce-superimage /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library superimage --test-malicious && \
docker compose run enforce-tner /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library tner --test-malicious && \
docker compose run enforce-tweetnlp /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library tweetnlp --test-malicious && \
docker compose run enforce-yolov5 /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library yolov5 --test-malicious && \
docker compose run enforce-yolov11 /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library yolov11 --test-malicious