#!/bin/bash
set -e

# The script to run should be mounted at /workspace/code.py
if [ ! -f "/workspace/code.py" ]; then
    echo "Error: /workspace/code.py not found." >&2
    exit 1
fi

python /workspace/code.py
