#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-/mnt/c/tmp/sphinx-docx}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PS1_LINUX="$REPO_ROOT/scripts/update-fields.ps1"
PS1_WIN="$(wslpath -w "$PS1_LINUX")"

shopt -s nullglob
files=("$OUT_DIR"/*.docx)
if (( ${#files[@]} == 0 )); then
  echo "No .docx files found in: $OUT_DIR" >&2
  exit 1
fi

for f in "${files[@]}"; do
  powershell.exe -NoProfile -ExecutionPolicy Bypass \
    -File "$PS1_WIN" \
    "$(wslpath -w "$f")"
done

