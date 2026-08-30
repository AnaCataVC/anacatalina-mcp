# ==============================================================================
# Dockerfile - Ana Catalina MCP Interactive Curriculum Server
# Optimized for Google Cloud Run (Serverless Container)
# ==============================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files & enable immediate log output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install minimal system utilities for health check if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and data
COPY . .

# Expose default Cloud Run port
EXPOSE 8080

# Run uvicorn respecting dynamic Cloud Run $PORT
CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
