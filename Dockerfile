# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for PyMuPDF (offline compatible)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libjpeg-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies (all downloaded during build for offline operation)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY extract_text.py .
COPY format.py .
COPY main.py .

# Set environment variables for offline operation
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Create input and output directories with proper permissions
RUN mkdir -p /app/input /app/output && \
    chown -R app:app /app && \
    chmod 755 /app/input /app/output

USER app

# Default command - process all PDFs from input to output
CMD ["python", "main.py"]
