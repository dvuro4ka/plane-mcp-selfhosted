FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv sync --frozen

COPY server.py .

ENV PATH="/app/.venv/bin:$PATH"
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=8000

EXPOSE 8000

CMD ["python", "server.py"]
