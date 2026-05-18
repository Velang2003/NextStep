FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy model
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 5000

# Start command (Overridden by docker-compose for worker/scheduler)
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 3 --timeout 120 wsgi:app
