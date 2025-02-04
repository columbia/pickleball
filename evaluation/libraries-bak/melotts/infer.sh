
#!/bin/bash

# Assumes execution from within the docker
# container, with mount points at /pickle-defense.
# be modified.

# Create CPG
/joern/joern-cli/target/universal/stage/pysrc2cpg \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    /pickle-defense/evaluation/libraries/melotts/MeloTTS/melo/ \
    -o /pickle-defense/evaluation/libraries/melotts/melotts.cpg

# Run analyze.sc script
/joern/joern --script /pickle-defense/analyze/analyze.sc \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    --param inputPath=/pickle-defense/evaluation/libraries/melotts/melotts.cpg \
    --param modelClass="api.py:<module>.TTS" \
    --param cache=/pickle-defense/evaluation/cache/ \
    --param outputPath=/pickle-defense/evaluation/libraries/melotts/models/TTS/policy.json \
    > /pickle-defense/evaluation/libraries/melotts/models/TTS/policy.log
