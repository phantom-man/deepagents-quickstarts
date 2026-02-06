# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for geopandas/gdal
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker cache)
COPY environmental_monitoring/backend/requirements.txt .

# Install core Python dependencies (skip heavy ML libs for now)
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    sqlalchemy==2.0.23 \
    aiosqlite==0.19.0 \
    redis==5.0.1 \
    pandas==2.1.4 \
    numpy==1.26.2 \
    scikit-learn==1.3.2 \
    geopandas==0.14.1 \
    shapely==2.0.2 \
    folium==0.15.1 \
    pyproj==3.6.1 \
    httpx==0.25.2 \
    aiohttp==3.9.1 \
    requests==2.31.0 \
    python-dotenv==1.0.0 \
    python-multipart==0.0.6 \
    matplotlib==3.8.2 \
    plotly==5.17.0

# Copy the application code
COPY environmental_monitoring/backend/ ./

# Set Python path
ENV PYTHONPATH=/app

# Expose port (Cloud Run uses 8080)
EXPOSE 8080

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
