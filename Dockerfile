# Use official Python runtime as base image
# This is like starting with a clean Linux system with Python pre-installed
FROM python:3.12-slim

# Set metadata about the image
LABEL maintainer="kamblepratik1404@gmail.com"
LABEL description="DevOps Todo Application"

# Set working directory inside container
# All commands will run from this directory
WORKDIR /app

# Copy requirements file first (Docker caching optimization)
# If requirements.txt doesn't change, Docker reuses this layer
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir = Don't store pip cache (smaller image)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Copy app folder and its contents
COPY app/ ./app/

# Copy tests and configuration files
COPY tests/ ./tests/
COPY pytest.ini .

# Create directory for data persistence
RUN mkdir -p /app/data

# Expose port 5000 to the outside world
# This tells Docker: "This app uses port 5000"
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app/app.py
ENV PYTHONUNBUFFERED=1

# Health check - Docker will periodically check if app is healthy
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Command to run when container starts
# This is the default command (can be overridden)
CMD ["python", "app/app.py"]