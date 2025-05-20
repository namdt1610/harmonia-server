#!/bin/sh
set -e

export PYTHONPATH=/app
export DISABLE_DEV_SHM_USAGE=1
export NO_SANDBOX=1

# Wait for postgres to be ready
if [ "$WAIT_FOR_DB" = "true" ]; then
    echo "Waiting for postgres..."
    while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
        sleep 2
    done
    echo "PostgreSQL started"
fi

# Apply migrations
python manage.py migrate --noinput

# Run gunicorn in production or runserver in development
if [ "$DJANGO_ENV" = "production" ]; then
    echo "Starting Gunicorn server in production mode"
    gunicorn spotify.wsgi:application --bind 0.0.0.0:8000 --workers=4 --timeout=120
else
    echo "Starting Django development server"
    python manage.py runserver 0.0.0.0:8000
fi
