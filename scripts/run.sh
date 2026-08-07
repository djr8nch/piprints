#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_EXECUTABLE="$PROJECT_ROOT/.venv/bin/python"

if [ ! -x "$PYTHON_EXECUTABLE" ]; then
    echo "PiPrints is not installed. Run ./scripts/install.sh first." >&2
    exit 1
fi

exec "$PYTHON_EXECUTABLE" -m piprints "$@"
