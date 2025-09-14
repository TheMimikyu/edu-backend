# syntax=docker/dockerfile:1

# --- Builder Stage ---
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /usr/src/app

# System deps (add build-essential if you need to compile native extensions)
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy dependency specification first for better caching
COPY pyproject.toml ./
# Copy lock file if it exists (won't fail if absent)
COPY uv.lock* ./

# Create virtual environment & install deps (use --frozen if lock present)
# If uv.lock exists this is reproducible; otherwise it resolves fresh.
RUN if [ -f uv.lock ]; then uv sync --frozen --no-install-project; else uv sync --no-install-project; fi

# Now copy project source to install the project itself (editable style not needed in final image)
COPY src ./src

# Install the project (adds your package to the venv)
RUN uv pip install --no-cache-dir ./src

# --- Final Stage ---
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Node.js and npm (for ESLint part)
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system app && adduser --system --group app --home /home/app --shell /bin/bash

# ESLint setup
WORKDIR /opt/eslint-setup
COPY ./src/agents/code_checker/package.json ./src/agents/code_checker/eslint.config.js ./
RUN npm install && chown -R app:app /opt/eslint-setup && chmod -R 755 /opt/eslint-setup

# App workdir
WORKDIR /home/app/web

# Copy virtual environment from builder
COPY --from=builder /usr/src/app/.venv ./.venv

# Copy metadata & source
COPY pyproject.toml ./
COPY src ./app

# Ensure permissions
RUN mkdir -p /home/app/.npm /home/app/.config \
    && chown -R app:app /home/app /home/app/web

USER app

# Environment so the venv is used
ENV PATH="/home/app/web/.venv/bin:${PATH}" \
    NPM_CONFIG_CACHE=/home/app/.npm \
    NPM_CONFIG_PREFIX=/home/app/.npm-global
ENV PATH=/home/app/.npm-global/bin:$PATH

EXPOSE 8000

# Use python from venv implicitly via PATH
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-1}