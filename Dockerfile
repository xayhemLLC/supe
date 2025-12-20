# Supe - Containerized Deployment
# Build: docker build -t supe .
# Run:   docker run -it supe status

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TASC_DB=/app/data/tasc.sqlite

# Create app user for security
RUN groupadd --gid 1000 supe && \
    useradd --uid 1000 --gid supe --shell /bin/bash --create-home supe

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY --chown=supe:supe . .

# Install uv for fast package management
RUN pip install --no-cache-dir uv

# Install the package
RUN uv pip install --system -e .

# Create data directory for persistence
RUN mkdir -p /app/data && chown supe:supe /app/data

# Switch to non-root user
USER supe

# Default entrypoint
ENTRYPOINT ["supe"]

# Default command (show help)
CMD ["--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD supe status || exit 1

# Labels
LABEL org.opencontainers.image.title="Supe" \
      org.opencontainers.image.description="AB Memory Engine and TASC Task Management System" \
      org.opencontainers.image.vendor="Chris Cabral" \
      org.opencontainers.image.licenses="MIT"
