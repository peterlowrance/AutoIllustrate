#!/bin/bash

if [[ ! -e env ]]; then
    echo "Creating python env"
    python3 -m venv env
    pip install -r requirements.txt
fi

source env/bin/activate

python auto_illustrator.py "$@"