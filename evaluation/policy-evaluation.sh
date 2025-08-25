#!/bin/bash

cd /pickleball/evaluation/

# Fetch all evaluation libraries
setup/fetch.sh

# Generate all evaluation library policies and output LaTeX table
python3 generate-policies.py manifest.toml
