FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directory
RUN mkdir -p .cache

# Expose port (Cloud Run sets PORT=8080)
EXPOSE 8080

# Environment variables
ENV DEBUG=False
ENV API_BASE_URL=https://env-monitor-api-758343025648.us-central1.run.app

# Run with gunicorn for production - use PORT env var from Cloud Run
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:server
