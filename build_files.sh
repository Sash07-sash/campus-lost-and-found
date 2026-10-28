#!/bin/bash
set -e

echo "--- Starting Vercel Build ---"
mkdir -p staticfiles

# Detect Python interpreter (priority: python3.12, python3, python)
if command -v python3.12 >/dev/null 2>&1; then
  PY_EXEC="python3.12"
elif command -v python3 >/dev/null 2>&1; then
  PY_EXEC="python3"
elif command -v python >/dev/null 2>&1; then
  PY_EXEC="python"
else
  PY_EXEC="python3"
fi

echo "Using Python interpreter: $PY_EXEC"
$PY_EXEC --version || true

echo "Installing project dependencies..."
# 1. If uv is available, explicitly target $PY_EXEC environment
if command -v uv >/dev/null 2>&1; then
  echo "Installing with uv for $PY_EXEC..."
  uv pip install -r requirements.txt --python "$PY_EXEC" --system || true
fi

# 2. Also ensure dependencies are installed directly via $PY_EXEC pip
echo "Installing directly with $PY_EXEC pip..."
$PY_EXEC -m pip install -r requirements.txt --break-system-packages || $PY_EXEC -m pip install -r requirements.txt || true

# 3. Verify Django is accessible in $PY_EXEC
echo "Verifying Django installation..."
$PY_EXEC -c "import django; print('Django version successfully loaded:', django.__version__)" || true

echo "Collecting static assets..."
$PY_EXEC manage.py collectstatic --noinput --clear || true

mkdir -p staticfiles
echo "--- Vercel Build Finished Successfully ---"
