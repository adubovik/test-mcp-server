FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

WORKDIR /app

COPY . .

RUN uv venv .venv
RUN uv sync

EXPOSE 5000

CMD ["uv", "run", "mcp-server-time"]
