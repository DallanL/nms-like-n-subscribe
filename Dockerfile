# Base Python image
FROM python:3.11-alpine AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set a working directory
WORKDIR /ns-subscriber

# Install only the necessary system dependencies
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY ./app ./app
COPY run.py ./

# Expose the application port (adjust as needed)
EXPOSE 8001

# Start the application
CMD ["python", "run.py"]

