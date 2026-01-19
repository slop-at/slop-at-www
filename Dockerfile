FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY server.py ./
COPY static ./static

# Install dependencies
RUN uv sync --frozen

# Create data directory
RUN mkdir -p /data/slops /data/oxigraph

# Set environment variables
ENV SLOP_HOME=/data
ENV OXIGRAPH_URL=http://oxigraph:7878

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
