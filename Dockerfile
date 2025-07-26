# Stage 1: Build stage with all dependencies
FROM python:3.11-alpine AS builder

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    jpeg-dev \
    freetype-dev \
    && rm -rf /var/cache/apk/*

# Copy requirements and install Python packages to a specific directory
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/install -r requirements.txt \
    && apk del .build-deps

# Stage 2: Final runtime stage
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install only essential runtime dependencies
RUN apk add --no-cache \
    jpeg \
    freetype \
    libstdc++ \
    && rm -rf /var/cache/apk/*

# Copy Python packages from builder stage
COPY --from=builder /install /usr/local/lib/python3.11/site-packages

# Copy application code
COPY extract_text.py .
COPY format.py .
COPY main.py .

# Set environment variables for offline operation
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Create a non-root user for security
RUN adduser -D -s /bin/sh app

# Create input and output directories with proper permissions
RUN mkdir -p /app/input /app/output && \
    chown -R app:app /app && \
    chmod 755 /app/input /app/output

USER app

# Default command - process all PDFs from input to output
CMD ["python", "main.py"]
