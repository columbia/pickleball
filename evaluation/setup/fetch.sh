#!/bin/bash

# TODO: Check if libraries have already been fetched, and either no-op or print
# warning.

SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALUATION_DIR="$SETUP_DIR/../"
LIBRARIES_DIR="$EVALUATION_DIR/libraries"

clone_and_checkout() {
    local repo_url=$1
    local repo_name=$2
    local commit_hash=$3
    local apply_diff=$4

    cd "$LIBRARIES_DIR" || return 1
    git clone --recurse-submodules "$repo_url" "$repo_name" || return 1
    cd "$repo_name" || return 1
    git checkout "$commit_hash" || return 1

    # Run extra command if provided
    if [[ -n "$apply_diff" ]]; then
	echo "applying diff"
        git apply $SETUP_DIR/$apply_diff
    fi
}

# Checkout repository URL, cd into directory, checkout commit, [optionally apply diff]
clone_and_checkout https://github.com/mahmoodlab/CONCH.git CONCH 02d6ac5
# The original FlagEmbedding evaluation used the 2bfc922 commit, but the
# library has been significantly rewritten and the git commit history has been
# overwritten. We have identified the bf6b649 commit as being close to the
# library state when we did our evaluation.
clone_and_checkout https://github.com/FlagOpen/FlagEmbedding.git FlagEmbedding bf6b649
clone_and_checkout https://github.com/flairNLP/flair.git flair c674212 flair.diff
clone_and_checkout https://github.com/urchade/GLiNER.git GLiNER 1169120
clone_and_checkout https://github.com/jonatasgrosman/huggingsound.git huggingsound 50e9fba
clone_and_checkout https://github.com/PKU-YuanGroup/LanguageBind.git LanguageBind 7070c53
clone_and_checkout https://github.com/myshell-ai/MeloTTS.git MeloTTS 5b53848
clone_and_checkout https://github.com/PrithivirajDamodaran/Parrot_Paraphraser.git Parrot_Paraphraser 03084c5
clone_and_checkout https://github.com/pyannote/pyannote-audio.git pyannote-audio 0ea4c02 pyannote.diff
clone_and_checkout https://github.com/pysentimiento/pysentimiento.git pysentimiento 60822ac
clone_and_checkout https://github.com/UKPLab/sentence-transformers.git sentence-transformers a1db32d sentence-transformers.diff
clone_and_checkout https://github.com/eugenesiow/super-image.git super-image 50439ea
clone_and_checkout https://github.com/asahi417/tner.git tner 7730a62
clone_and_checkout https://github.com/cardiffnlp/tweetnlp.git tweetnlp 68b08c8
clone_and_checkout https://github.com/fcakyon/yolov5-pip.git yolov5 40a1887
clone_and_checkout https://github.com/ultralytics/ultralytics.git yolov11 b18007e
