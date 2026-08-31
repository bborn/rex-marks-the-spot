#!/usr/bin/env bash
#
# Create (or refresh) the project's Python environment.
#
# This replaces the ad-hoc "/tmp venv for Omni" situation: there is one
# environment, pinned in requirements.txt, that every generation script runs in.
#
#   ./scripts/setup_python_env.sh            # create/refresh .venv
#   ./scripts/setup_python_env.sh --check    # verify only, don't install
#   ./scripts/setup_python_env.sh --path DIR # use DIR instead of ./.venv
#
# Then either activate it:
#     source .venv/bin/activate
#     python scripts/video/run_omni_phase06.py ...
# or call it directly:
#     .venv/bin/python scripts/video/run_omni_phase06.py ...
#
# Background: docs/research/sdk-migration-decision.md
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
CHECK_ONLY=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check) CHECK_ONLY=1; shift ;;
        --path)  VENV_DIR="$2"; shift 2 ;;
        -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
done

PY="${PYTHON:-python3}"

if [[ "$CHECK_ONLY" -eq 0 ]]; then
    if [[ ! -x "$VENV_DIR/bin/python" ]]; then
        echo "==> Creating virtualenv at $VENV_DIR"
        "$PY" -m venv "$VENV_DIR"
    else
        echo "==> Reusing virtualenv at $VENV_DIR"
    fi

    echo "==> Installing $REPO_ROOT/requirements.txt"
    "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
    "$VENV_DIR/bin/python" -m pip install --quiet -r "$REPO_ROOT/requirements.txt"
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "ERROR: no environment at $VENV_DIR - run without --check first." >&2
    exit 1
fi

VENV_PY="$VENV_DIR/bin/python"

echo "==> Verifying the SDK version"
"$VENV_PY" - <<'PYEOF'
import sys
from google import genai

major = int(genai.__version__.split(".")[0])
print(f"    google-genai {genai.__version__}  (python {sys.version.split()[0]})")
if major < 2:
    sys.exit(
        "ERROR: google-genai >= 2.0.0 is required.\n"
        "       1.x sends the legacy Interactions wire format that Google\n"
        "       retired in May 2026, so every Gemini Omni call fails."
    )
PYEOF

echo "==> Running the offline SDK compatibility suite (no network, no spend)"
( cd "$REPO_ROOT/scripts" && "$VENV_PY" -m pytest test_sdk_compat.py -q )

echo
echo "Environment ready: $VENV_DIR"
echo "  source ${VENV_DIR#"$REPO_ROOT"/}/bin/activate"
