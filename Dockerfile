# ── Stage 1: Build React frontend ─────────────────────────────────────────
FROM node:22-slim AS frontend

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --legacy-peer-deps 2>/dev/null || npm install --legacy-peer-deps

COPY frontend/ .
# Build the SPA into src/OpenDEMON/server/static (matches vite.config.ts outDir)
RUN npm run build || (npm install react-is && npm run build)

# ── Stage 2: Python runtime ────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy Python package files
COPY pyproject.toml README.md render_start.py ./
COPY src/ src/

# Copy built frontend static files into the server static directory
COPY --from=frontend /app/src/OpenDEMON/server/static src/OpenDEMON/server/static/

# Install the package with server extras (no Rust extension needed for web deploy)
RUN uv pip install --system ".[server]"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the server
CMD ["python", "render_start.py"]
