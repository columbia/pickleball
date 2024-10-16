#!/bin/bash

# Create CPG
/joern/joern-cli/target/universal/stage/pysrc2cpg \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    /pickle-defense/evaluation/libraries/pyannote-audio/pyannote-audio/ \
    -o /pickle-defense/evaluation/libraries/pyannote-audio/pyannote.cpg \
    --ignore-paths="/pickle-defense/evaluation/libraries/pyannote-audio/pyannote-audio/tests/,/pickle-defense/evaluation/libraries/pyannote-audio/pyannode-audio/tutorials/"

# Run analyze.sc script
/joern/joern --script /pickle-defense/analyze/analyze.sc \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    --param inputPath=/pickle-defense/evaluation/libraries/pyannote-audio/out.cpg \
    --param modelClass="pyannote/audio/models/embedding/wespeaker/__init__.py:<module>.WeSpeakerResNet34" \
    --param cache=/pickle-defense/evaluation/cache/ \
    --param outputPath=/pickle-defense/evaluation/libraries/pyannote-audio/models/WeSpeakerResNet34/policy.json
