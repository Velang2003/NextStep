#!/bin/bash

# Start the Gunicorn web server
# Pipeline runs automatically via APScheduler (no separate Celery worker needed)
echo "Starting Gunicorn server..."
gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 3 --timeout 120 wsgi:app
