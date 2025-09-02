#!/bin/bash

docker compose build pickleball-generate && \
docker compose build pickleball-enforce && \
docker compose build pickleball-enforce-deb11 && \

docker compose build modelscan && \
docker compose build modeltracer && \
docker compose build weightsonly && \

docker compose build enforce-conch && \
docker compose build enforce-flagembedding && \
docker compose build enforce-flair && \
docker compose build enforce-gliner && \
docker compose build enforce-huggingsound && \
docker compose build enforce-languagebind && \
docker compose build enforce-melotts && \
docker compose build enforce-parrot && \
docker compose build enforce-pyannote && \
docker compose build enforce-pysentimiento && \
docker compose build enforce-sentencetransformers && \
docker compose build enforce-superimage && \
docker compose build enforce-superimage && \
docker compose build enforce-tner && \
docker compose build enforce-tweetnlp && \
docker compose build enforce-yolov5 && \
docker compose build enforce-yolov11 && \

docker compose build control-load && \
docker compose build control-load-deb11 && \

docker compose build weightsonly-load-conch && \
docker compose build weightsonly-load-flagembedding && \
docker compose build weightsonly-load-flair && \
docker compose build weightsonly-load-gliner && \
docker compose build weightsonly-load-huggingsound && \
docker compose build weightsonly-load-languagebind && \
docker compose build weightsonly-load-melotts && \
docker compose build weightsonly-load-parrot && \
docker compose build weightsonly-load-pyannote && \
docker compose build weightsonly-load-pysentimiento && \
docker compose build weightsonly-load-sentencetransformers && \
docker compose build weightsonly-load-superimage && \
docker compose build weightsonly-load-superimage && \
docker compose build weightsonly-load-tner && \
docker compose build weightsonly-load-tweetnlp && \
docker compose build weightsonly-load-yolov5 && \
docker compose build weightsonly-load-yolov11 && \

docker compose build control-load-time-conch && \
docker compose build control-load-time-flagembedding && \
docker compose build control-load-time-flair && \
docker compose build control-load-time-gliner && \
docker compose build control-load-time-huggingsound && \
docker compose build control-load-time-languagebind && \
docker compose build control-load-time-melotts && \
docker compose build control-load-time-parrot && \
docker compose build control-load-time-pyannote && \
docker compose build control-load-time-pysentimiento && \
docker compose build control-load-time-sentencetransformers && \
docker compose build control-load-time-superimage && \
docker compose build control-load-time-superimage && \
docker compose build control-load-time-tner && \
docker compose build control-load-time-tweetnlp && \
docker compose build control-load-time-yolov5 && \
docker compose build control-load-time-yolov11 && \

docker compose build enforce-load-time-conch && \
docker compose build enforce-load-time-flagembedding && \
docker compose build enforce-load-time-flair && \
docker compose build enforce-load-time-gliner && \
docker compose build enforce-load-time-huggingsound && \
docker compose build enforce-load-time-languagebind && \
docker compose build enforce-load-time-melotts && \
docker compose build enforce-load-time-parrot && \
docker compose build enforce-load-time-pyannote && \
docker compose build enforce-load-time-pysentimiento && \
docker compose build enforce-load-time-sentencetransformers && \
docker compose build enforce-load-time-superimage && \
docker compose build enforce-load-time-superimage && \
docker compose build enforce-load-time-tner && \
docker compose build enforce-load-time-tweetnlp && \
docker compose build enforce-load-time-yolov5 && \
docker compose build enforce-load-time-yolov11
