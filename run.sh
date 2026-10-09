#!/usr/bin/env bash
set -euo pipefail
project_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export PYTHONPATH="$project_root/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m linux_control "$@"
