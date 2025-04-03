#!/bin/bash

# Create CPG
/joern/joern-cli/target/universal/stage/pysrc2cpg \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    /pickle-defense/evaluation/libraries/pyannote-audio/pyannote-audio/ \
    -o /pickle-defense/evaluation/libraries/pyannote-audio/pyannote.cpg \
    --ignore-paths="/pickle-defense/evaluation/libraries/pyannote-audio/pyannote-audio/tests/,/pickle-defense/evaluation/libraries/pyannote-audio/pyannode-audio/tutorials/"

# Run analyze.sc script for the Model class policy
/joern/joern --script /pickle-defense/analyze/analyze.sc \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    --param inputPath=/pickle-defense/evaluation/libraries/pyannote-audio/pyannote.cpg \
    --param modelClass="pyannote/audio/core/model.py:<module>.Model" \
    --param cache=/pickle-defense/evaluation/cache/ \
    --param outputPath=/pickle-defense/evaluation/libraries/pyannote-audio/models/Model/policy.json \
    > /pickle-defense/evaluation/libraries/pyannote-audio/models/Model/policy.log
