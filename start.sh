#!/usr/bin/env sh
# One command setup for Linux and macOS. Extra arguments go to start.py.
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found: install Python 3.10 or newer"
    exit 1
fi
exec python3 start.py "$@"
