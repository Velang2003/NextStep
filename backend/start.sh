#!/bin/bash

# Start Gunicorn with a single worker to stay within Render's 512MB free tier.
# APScheduler runs inside this process — no separate Celery/Redis needed.
echo "Starting Gunicorn server..."
gunicorn \
  --bind 0.0.0.0:${PORT:-5000} \
  --workers 1 \
  --threads 4 \
  --worker-class gthread \
  --timeout 180 \
  --max-requests 500 \
  --max-requests-jitter 50 \
  wsgi:app
