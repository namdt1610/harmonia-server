#!/bin/sh
set -e

export PYTHONPATH=/app
export DISABLE_DEV_SHM_USAGE=1
export NO_SANDBOX=1
export DJANGO_SETTINGS_MODULE=spotify.settings_render

# Wait for postgres to be ready
echo "Waiting for postgres..."
max_retries=30
retry_count=0

# Print database connection details for debugging
echo "Database connection details:"
echo "Host: $DB_HOST"
echo "Port: $DB_PORT"
echo "User: $DB_USER"
echo "Database: $DB_NAME"

while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
        echo "Could not connect to PostgreSQL after $max_retries attempts. Exiting..."
        exit 1
    fi
    echo "Attempt $retry_count: PostgreSQL not ready yet... waiting"
    sleep 2
done
echo "PostgreSQL started"

# Apply migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Start Gunicorn
echo "Starting Gunicorn server on Render"
exec gunicorn spotify.wsgi:application --bind 0.0.0.0:$PORT --workers=4 --timeout=120 