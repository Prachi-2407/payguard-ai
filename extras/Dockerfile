FROM python:3.12-slim

# Working directory
WORKDIR /app

# Prevent Python from writing .pyc and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV PYTHONPATH=/app

# Install system dependencies including build tools and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY extras/requirements.txt /app/extras/requirements.txt
RUN pip install --no-cache-dir -r /app/extras/requirements.txt

# Copy source code and sample data
COPY extras /app/extras
COPY sample_data /app/sample_data

# Pre-train or ensure model artifacts exist
RUN python -m extras.ml.train

# Expose port for Extras Intelligence Layer
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/api/ext/health || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "extras.app.main:app", "--host", "0.0.0.0", "--port", "8001"]

