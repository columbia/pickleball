#!/bin/bash

docker compose run enforce-conch /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-conch --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-flagembedding /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-flagembedding --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-flair /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-flair --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-gliner /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-gliner --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-huggingsound /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-huggingsound --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-languagebind /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-languagebind --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-melotts /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-melotts --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-parrot /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-parrot --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-pyannote /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-pyannote --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-pysentimiento /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-pysentimiento --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-sentencetransformers /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-sentencetransformers --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-superimage /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-superimage --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-tner /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-tner --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-tweetnlp /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-tweetnlp --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-yolov5 /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-yolov5 --output-dir /pickleball/evaluation/enforcement/results-malicious && \
docker compose run enforce-yolov11 /pickleball/evaluation/enforcement/load_all.py --all-model-path /models/malicious --library malicious-yolov11 --output-dir /pickleball/evaluation/enforcement/results-malicious
