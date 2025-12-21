# Multi-stage build for optimized production image
# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to user directory
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only (WeasyPrint for PDF generation)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8383/health || exit 1

# Expose port
EXPOSE 8383

# Environment variables for runtime configuration
ENV WORKERS=1
ENV PORT=8383
ENV LOG_LEVEL=info

# Run with configurable workers (default 1 for async app)
# Using shell form to allow variable substitution
CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS} --log-level ${LOG_LEVEL}
