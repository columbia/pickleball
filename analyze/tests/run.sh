#!/bin/bash

# For each sub-directory in the pickle-defense/analyze/tests/ directory:
# - Assume subdir has src/ directory containing test target.
# - Assume subdir has models/ directory containing class subdirectories
#   - Each class subdir contains: one or more .pkl file
#   - Each class subdir contains a 'metadata' file containing the Joern
#     fullname for the class type decl.
# - Generate fickling trace and json policy description for each model
#   - input: subdir/class/*.pkl
#   - output: subdir/class/*.trace
#   - output: subdir/class/*.json
# - Generate the fixture baseline policy for each class
#   (union of all policies generated per model)
#   - input: subdir/class/*.json
#   - input: subdir/class/metadata
#   - output: subdir/class/baseline.json
# - Generate Joern CPG
#   - input: subdir/src/
#   - output: subdir/out.cpg
# - Generate inferred policy for each class
#   - input: subdir/out.cpg
#   - input: subdir/*/metadata
#   - output: subdir/*/inferred.json
# - Report F1 score for each inferred policy compared to baseline:
#   - input: subdir/*/inferred.json
#   - input: subdir/*/baseline.json
#   - output: subdir/*/result.json
