#!/bin/bash

# Assumes execution from within the docker
# container, with mount points at /pickle-defense.
# be modified.

# Create CPG
/joern/joern-cli/target/universal/stage/pysrc2cpg \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    /pickle-defense/evaluation/libraries/languagebind/LanguageBind/ \
    -o /pickle-defense/evaluation/libraries/languagebind/languagebind.cpg

# Run analyze.sc script
/joern/joern --script /pickle-defense/analyze/analyze.sc \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    --param inputPath=/pickle-defense/evaluation/libraries/languagebind/languagebind.cpg \
    --param modelClass="languagebind/__init__.py:<module>.LanguageBind" \
    --param cache=/pickle-defense/evaluation/cache/ \
    --param outputPath=/pickle-defense/evaluation/libraries/languagebind/models/LanguageBind/policy.json \
    > /pickle-defense/evaluation/libraries/languagebind/models/LanguageBind/policy.log
