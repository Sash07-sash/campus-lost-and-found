#!/bin/bash
set -e

echo "--- Starting Vercel Build ---"
mkdir -p staticfiles

# Detect Python interpreter
if command -v python3.12 >/dev/null 2>&1; then
  PY_EXEC="python3.12"
elif command -v python3 >/dev/null 2>&1; then
  PY_EXEC="python3"
elif command -v python >/dev/null 2>&1; then
  PY_EXEC="python"
else
  PY_EXEC="python3"
fi

echo "Using Python: $PY_EXEC"
$PY_EXEC --version || true

echo "Installing project dependencies..."
if command -v uv >/dev/null 2>&1; then
  echo "Using uv to install packages into system environment..."
  uv pip install -r requirements.txt --system || uv pip install -r requirements.txt
else
  $PY_EXEC -m pip install -r requirements.txt --break-system-packages || $PY_EXEC -m pip install -r requirements.txt
fi

echo "Collecting static assets..."
$PY_EXEC manage.py collectstatic --noinput --clear || true

mkdir -p staticfiles
echo "--- Vercel Build Finished Successfully ---"
