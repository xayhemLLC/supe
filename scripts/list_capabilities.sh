#!/bin/bash
# List all problem solver capabilities

cd "$(dirname "$0")/.." || exit
python3 -c "import sys; sys.path.insert(0, '.'); from supe.reasoning.scripts.list_capabilities import main; main()"
