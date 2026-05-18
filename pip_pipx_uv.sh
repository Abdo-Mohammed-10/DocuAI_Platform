#!/bin/bash

curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

curl -LsSf https://astral.sh/uv/install.sh | sh

uv --version