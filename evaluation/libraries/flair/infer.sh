#!/bin/bash

# Assumes execution from within the docker
# container, with mount points at /pickle-defense.
# be modified.

# Create CPG
/joern/joern-cli/target/universal/stage/pysrc2cpg \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    /pickle-defense/evaluation/libraries/flair/flair/ \
    -o /pickle-defense/evaluation/libraries/flair/flair.cpg \
    --ignore-paths="/pickle-defense/evaluation/libraries/flair/flair/tests/,/pickle-defense/evaluation/libraries/flair/flair/examples/,/pickle-defense/evaluation/libraries/flair/flair/flair/datasets"

# Run analyze.sc script
/joern/joern --script /pickle-defense/analyze/analyze.sc \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    --param inputPath=/pickle-defense/evaluation/libraries/flair/flair.cpg \
    --param modelClass="flair/models/sequence_tagger_model.py:<module>.SequenceTagger" \
    --param cache=/pickle-defense/evaluation/cache/ \
    --param outputPath=/pickle-defense/evaluation/libraries/flair/models/SequenceTagger/policy.json
