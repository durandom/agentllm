# SPDX-FileCopyrightText: © 2025 Christoph Görn <goern@goern.name>
# SPDX-License-Identifier: GPL-3.0-only

FROM python:3.13-slim AS builder

# Install system dependencies including curl for healthchecks and build tools for html-to-markdown
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy all source files needed for build
COPY . ./

# Install the package and dependencies using uv
RUN  uv pip install --system --no-cache . 

# Runtime stage
FROM python:3.13-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed dependencies from builder (including agentllm package)
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create directories for data persistence
RUN mkdir -p /app/tmp/gdrive_workspace

# Set Python environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose LiteLLM proxy port
EXPOSE 8890

# Run LiteLLM with custom config
CMD ["litellm", "--config", "/usr/local/lib/python3.13/site-packages/agentllm/proxy_config.yaml", "--port", "8890", "--host", "0.0.0.0"]
