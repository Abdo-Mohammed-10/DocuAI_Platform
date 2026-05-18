#!/bin/bash

find services shared frontend -type d | while read dir; do
  touch "$dir/__init__.py"
done