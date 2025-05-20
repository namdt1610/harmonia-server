#!/bin/bash
# Script to run Django server directly with Chrome sandbox disabled

# Set environment variables
export PYTHONPATH=$(pwd)
export DISABLE_DEV_SHM_USAGE=1
export NO_SANDBOX=1
export PYTHONIOENCODING=utf-8
export DB_PASSWORD=nam

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Django development server on localhost
echo "Starting Django development server..."
python3 manage.py runserver 127.0.0.1:8001 