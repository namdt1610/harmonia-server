#!/bin/bash

# Activate the virtual environment
source /home/namdt/Code/spotify.django.backend/venv/bin/activate

# Go to project directory
cd /home/namdt/Code/spotify.django.backend

# Run the cleanup script
python manage.py cleanup_tokens 