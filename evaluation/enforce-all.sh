#!/bin/bash

docker compose run enforce-conch && \
docker compose run enforce-flagembedding && \
docker compose run enforce-flair && \
docker compose run enforce-gliner && \
docker compose run enforce-huggingsound && \
docker compose run enforce-languagebind && \
docker compose run enforce-melotts && \
docker compose run enforce-parrot && \
docker compose run enforce-pyannote && \
docker compose run enforce-pysentimiento && \
docker compose run enforce-sentencetransformers && \
docker compose run enforce-tner && \
docker compose run enforce-tweetnlp && \
docker compose run enforce-yolov5 && \
docker compose run enforce-yolov11
