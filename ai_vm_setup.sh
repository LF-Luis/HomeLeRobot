#!/bin/bash

# Setup lightweight env in VM to FT groot model
#
# Tested in Lambda Stack 22.04 (no filesystem attached needed). Or VESSL AI.
# How to run: bash hack_code/lambda_setup.sh

set -ex

wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
chmod +x Miniforge3-Linux-x86_64.sh
./Miniforge3-Linux-x86_64.sh -b -p $HOME/miniforge3

source $HOME/miniforge3/etc/profile.d/conda.sh
$HOME/miniforge3/bin/conda init bash
source ~/.bashrc

git clone https://github.com/NVIDIA/Isaac-GR00T
cd Isaac-GR00T

conda create -n gr00t python=3.10 -y
conda activate gr00t
pip install --upgrade setuptools
pip install -e .[base]
pip install --no-build-isolation flash-attn==2.7.1.post4
pip install hf_transfer

exec bash
