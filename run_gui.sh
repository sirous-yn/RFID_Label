#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
    echo "Project is not installed yet. Run: bash setup_linux.sh" >&2
    exit 1
fi
exec "$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/label_gui.py" "$@"
