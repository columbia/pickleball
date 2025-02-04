#!/bin/bash

# TODO: Check if libraries have already been fetched, and either no-op or print
# warning.

SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALUATION_DIR="$SETUP_DIR/../"
LIBRARIES_DIR="$EVALUATION_DIR/libraries"

# conch
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/mahmoodlab/CONCH.git
cd CONCH
git checkout 02d6ac5

# flagembedding
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/FlagOpen/FlagEmbedding.git
cd FlagEmbedding
# TODO: Investigate which commit is clostest to one we used in our experiments
#git checkout 2bfc922 # This is the commit we used, but it no longer exists
git checkout cbf98a6 # This is most recent commit, but with incorrect analysis results

# flair
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/flairNLP/flair.git
cd flair
git checkout c674212
git apply $SETUP_DIR/flair.diff

# gliner
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/urchade/GLiNER.git
cd GLiNER
git checkout 1169120

# huggingsound
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/jonatasgrosman/huggingsound.git
cd huggingsound
git checkout 50e9fba

# languagebind
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/PKU-YuanGroup/LanguageBind.git
cd LanguageBind
git checkout 7070c53

# melotts
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/myshell-ai/MeloTTS.git
cd MeloTTS
git checkout 5b53848

# parrot
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/PrithivirajDamodaran/Parrot_Paraphraser.git
cd Parrot_Paraphraser
git checkout 03084c5

# pyannote
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/pyannote/pyannote-audio.git
cd pyannote-audio
git checkout 0ea4c02
git apply $SETUP_DIR/pyannote.diff

# pysentimiento
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/pysentimiento/pysentimiento.git
cd pysentimiento
git checkout 60822ac

# sentence-transformers
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/UKPLab/sentence-transformers.git
cd sentence-transformers
git checkout a1db32d
git apply $SETUP_DIR/sentence-transformers.diff

# superimage
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/eugenesiow/super-image.git
cd super-image
git checkout 50439ea

# tner
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/asahi417/tner.git
cd tner
git checkout 7730a62

# tweetnlp
cd $LIBRARIES_DIR
git clone --recurse-submodules https://github.com/cardiffnlp/tweetnlp.git
cd tweetnlp
git checkout 68b08c8
