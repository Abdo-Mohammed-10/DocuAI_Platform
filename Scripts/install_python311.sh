#!/bin/bash

sudo apt install -y software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa -y

sudo apt update

sudo apt install -y python3.11 python3.11-venv python3.11-dev

python3.11 --version