#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

THEME_ASSEMBLER="tools/theme_assembler.py"
DEFAULT_SRC_DIR="src"
DEFAULT_THEMES_DIR="themes"
DEFAULT_FINAL_DIR="/config/themes/graphite-dev"
DEFAULT_THEME_NAME="Graphite"
DEV_MODE=1

SRC_DIR="${SRC_DIR:-$DEFAULT_SRC_DIR}"
THEMES_DIR="${THEMES_DIR:-$DEFAULT_THEMES_DIR}"
FINAL_DIR="${FINAL_DIR:-$DEFAULT_FINAL_DIR}"
THEME_NAME="${THEME_NAME:-$DEFAULT_THEME_NAME}"

if [ ! -f "${THEME_ASSEMBLER}" ]; then
    echo "Error: Theme assembler not found at '${THEME_ASSEMBLER}'"
    echo "WD: $(pwd)"
    exit 1
fi

echo "Building themes with the following configuration:"
echo "  Source directory: ${SRC_DIR}"
echo "  Themes directory: ${THEMES_DIR}"
echo "  Final directory: ${FINAL_DIR}"
echo "  Theme name: ${THEME_NAME}"
if [ -n "${DEV_MODE}" ]; then
    echo "  Dev mode: enabled"
fi

DEV_FLAG=""
if [ -n "${DEV_MODE}" ]; then
    DEV_FLAG="--dev"
fi

if python3 "${THEME_ASSEMBLER}" \
    --src-dir "${SRC_DIR}" \
    --themes-dir "${THEMES_DIR}" \
    --name "${THEME_NAME}" \
    --final-dir "${FINAL_DIR}" \
    ${DEV_FLAG}; then
    echo "Theme assembly and installation completed successfully"
else
    echo "Error: Theme assembly failed"
    exit 1
fi
