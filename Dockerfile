FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# ffmpeg: for video processing
# imagemagick: for image processing (if needed by moviepy)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY *.py ./

# Create directories for generated assets
RUN mkdir -p generated_assets/images generated_assets/audio generated_assets/videos

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "src.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
