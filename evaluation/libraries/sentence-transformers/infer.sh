#!/bin/bash

# Create CPG
/joern/joern-cli/target/universal/stage/pysrc2cpg \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    /pickle-defense/evaluation/libraries/sentence-transformers/sentence-transformers/sentence_transformers/ \
    -o /pickle-defense/evaluation/libraries/sentence-transformers/sentence-transformers.cpg

/joern/joern --script /pickle-defense/analyze/analyze.sc \
    -J-Xmx`grep MemTotal /proc/meminfo | awk '{print $2}'`k \
    --param inputPath=/pickle-defense/evaluation/libraries/sentence-transformers/sentence-transformers.cpg \
    --param modelClass="SentenceTransformer.py:<module>.SentenceTransformer" \
    --param cache=/pickle-defense/evaluation/cache/ \
    --param outputPath=/pickle-defense/evaluation/libraries/sentence-transformers/models/SentenceTransformer/policy.json \
    > /pickle-defense/evaluation/libraries/sentence-transformers/models/SentenceTransformer/policy.log
