#!/bin/bash

# Assumes execution from within the docker
# container, with mount points at /pickle-defense.
# be modified.

# Create CPG
/joern/joern-parse \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    /pickle-defense/evaluation/libraries/parrot/Parrot_Paraphraser/parrot/ \
    -o /pickle-defense/evaluation/libraries/parrot/parrot.cpg

# Run analyze.sc script
/joern/joern --script /pickle-defense/analyze/analyze.sc \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    --param inputPath=/pickle-defense/evaluation/libraries/parrot/parrot.cpg \
    --param modelClass="parrot.py:<module>.Parrot" \
    --param cache=/pickle-defense/evaluation/cache/ \
    --param outputPath=/pickle-defense/evaluation/libraries/parrot/models/Parrot/policy.json \
    > /pickle-defense/evaluation/libraries/parrot/models/Parrot/policy.log
