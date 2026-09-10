FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.11.21

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app/ app/
RUN mkdir -p data/uploads data/outputs data/knowledge data/workspace

ENV PYTHONUNBUFFERED=1
ENV KAVACH_HOST=0.0.0.0
ENV KAVACH_PORT=8000
ENV OLLAMA_HOST=http://host.docker.internal:11434

EXPOSE 8000

CMD [".venv/bin/python", "-m", "app.main"]
