#!/bin/bash

# Create CPG
/joern/joern-cli/target/universal/stage/pysrc2cpg \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    /pickle-defense/evaluation/libraries/super-image/super-image/src/ \
    -o /pickle-defense/evaluation/libraries/super-image/super-image.cpg

/joern/joern --script /pickle-defense/analyze/analyze.sc \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    --param inputPath=/pickle-defense/evaluation/libraries/super-image/super-image.cpg \
    --param modelClass="super_image/models/edsr/modeling_edsr.py:<module>.EdsrModel" \
    --param cache=/pickle-defense/evaluation/cache/ \
    --param outputPath=/pickle-defense/evaluation/libraries/super-image/models/EdsrModel/policy.json \
    > /pickle-defense/evaluation/libraries/super-image/models/EdsrModel/policy.log
