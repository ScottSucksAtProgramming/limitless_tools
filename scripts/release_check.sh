#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> Running ruff"
ruff check "${ROOT_DIR}"

echo "==> Running mypy"
mypy "${ROOT_DIR}/limitless_tools"

echo "==> Running pytest"
"${PYTHON_BIN}" -m pytest -q

echo "==> Building artifacts"
"${PYTHON_BIN}" -m build

echo "==> Running twine check"
"${PYTHON_BIN}" -m twine check dist/*

echo "==> Smoke testing wheel install"
SMOKE_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${SMOKE_DIR}"
}
trap cleanup EXIT

"${PYTHON_BIN}" -m venv "${SMOKE_DIR}/venv"
# shellcheck disable=SC1091
source "${SMOKE_DIR}/venv/bin/activate"
pip install --upgrade pip >/dev/null
pip install dist/*.whl >/dev/null
limitless --help >/dev/null
deactivate >/dev/null 2>&1 || true

echo "Release checks completed successfully."
