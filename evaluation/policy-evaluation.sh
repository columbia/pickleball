#!/bin/bash

# Fetch libraries
# TODO

cd /pickleball/evaluation/

# Generate all evaluation library policies
python3 generate-policies.py

# Generate table
python3 /pickleball/scripts/generatetable.py manifest.toml > tables/table.tex
cd tables/
pdflatex table.tex
