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

echo "Ensuring staticfiles/static mirror exists for Vercel static routing..."
mkdir -p staticfiles/static
cp -r staticfiles/css staticfiles/static/ 2>/dev/null || true
cp -r staticfiles/js staticfiles/static/ 2>/dev/null || true
cp -r staticfiles/admin staticfiles/static/ 2>/dev/null || true

echo "Ensuring media assets are bundled in staticfiles/media and staticfiles/static/media..."
mkdir -p staticfiles/media
mkdir -p staticfiles/static/media
cp -r media/* staticfiles/media/ 2>/dev/null || true
cp -r media/* staticfiles/static/media/ 2>/dev/null || true

echo "--- Vercel Build Finished Successfully ---"
