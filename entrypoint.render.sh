#!/bin/sh
set -e

export PYTHONPATH=/app
export DISABLE_DEV_SHM_USAGE=1
export NO_SANDBOX=1
export DJANGO_SETTINGS_MODULE=spotify.settings_render

# Wait for postgres to be ready
echo "Waiting for postgres..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    sleep 2
done
echo "PostgreSQL started"

# Apply migrations
python manage.py migrate --noinput

# Start Gunicorn
echo "Starting Gunicorn server on Render"
gunicorn spotify.wsgi:application --bind 0.0.0.0:$PORT --workers=4 --timeout=120 