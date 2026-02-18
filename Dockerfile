FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY . .

RUN uv venv .venv --no-managed-python
RUN uv sync

EXPOSE 5000

HEALTHCHECK  --interval=10s --timeout=5s --start-period=30s --retries=6 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1

CMD ["uv", "run", "mcp-server-time"]
