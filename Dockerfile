# Hugging Face Spaces Compatible Dockerfile for Multi-Agent Code Generator
FROM python:3.9-slim

# Create non-root user (HF requirement)
RUN useradd -m -u 1000 user
USER user

# Set environment variables
ENV PATH="/home/user/.local/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV HOST=0.0.0.0

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY --chown=user ./requirements.txt requirements.txt

# Install system dependencies and Python packages
USER root
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

USER user

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY --chown=user . /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/temp /app/uploads /app/static

# Expose the port (HF Spaces requirement)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

# Start the application
CMD ["python", "app.py"]