#!/bin/bash
echo "Installing project dependencies..."
python3.11 -m pip install -r requirements.txt

echo "Collecting static assets..."
python3.11 manage.py collectstatic --noinput --clear

echo "Build completed successfully!"
