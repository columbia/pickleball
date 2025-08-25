#!/bin/bash

libraries=("conch" "flair" "flagembedding" "gliner" "huggingsound" "languagebind" "melotts" "parrot" "pyannote" "pysentimiento" "sentencetransformers" "superimage" "tner" "tweetnlp" "yolov5" "yolov11")
versions=("control" "enforce")

for library in ${libraries[@]}; do
    for version in ${versions[@]}; do
        container="$version-load-time-$library"
        docker compose run $container
    done
done
