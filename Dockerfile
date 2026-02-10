FROM python:3.12-slim

# Install uv and curl for health checks with retry logic for network issues
RUN for i in 1 2 3 4 5; do \
        apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* && break || \
        (echo "Attempt $i failed, retrying in 10 seconds..." && sleep 10); \
    done || (echo "Failed to install curl after 5 attempts" && exit 1)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy all necessary files for building
COPY pyproject.toml uv.lock ./
COPY main.py ./
COPY app ./app

# Install dependencies with increased timeout
ENV UV_HTTP_TIMEOUT=120
RUN uv sync --frozen --no-cache

# Create a non-root user
RUN useradd -m -u 1001 fastapi && chown -R fastapi:fastapi /app

# Switch to non-root user
USER fastapi

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application
CMD ["/app/.venv/bin/python", "main.py"]