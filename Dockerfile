FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY . .

RUN uv venv .venv --no-managed-python
RUN uv sync

EXPOSE 5000

CMD ["uv", "run", "mcp-server-time"]
