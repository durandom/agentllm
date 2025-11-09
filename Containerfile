# SPDX-FileCopyrightText: © 2025 Christoph Görn <goern@goern.name>
# SPDX-License-Identifier: GPL-3.0-only

FROM python:3.13-slim AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy all source files needed for build
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package and dependencies using uv
RUN uv pip install --system --no-cache .

# Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Copy installed dependencies from builder (including agentllm package)
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source and config
COPY src/ ./src/

# Expose LiteLLM proxy port
EXPOSE 8890

# Run LiteLLM with custom config
CMD ["litellm", "--config", "src/agentllm/proxy_config.yaml", "--port", "8890"]