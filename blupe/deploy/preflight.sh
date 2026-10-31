#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
# Includes the actual command parser/generator/canonical-validator/wire gate.
# No physical session, model inference or outbound actuator transport is used.
exec env PYTHONPATH="$root/blupe" "${PYTHON:-python3}" -m pytest blupe/tests -q
