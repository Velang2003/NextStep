#!/bin/bash

# Start the Celery worker in the background
echo "Starting Celery worker..."
celery -A app.celery_app.celery_app worker --loglevel=info &

# Start the Gunicorn web server in the foreground
echo "Starting Gunicorn server..."
gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 3 --timeout 120 wsgi:app
