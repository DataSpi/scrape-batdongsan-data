FROM python:3.12-slim

# libpq-dev + gcc: build deps for psycopg2-binary/pyarrow wheels on slim base
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY dbt/ ./dbt/

# `data/` is gitignored (scrape output dumps), so a fresh clone/image has none --
# src/_web2br/*.py write CSV artifacts to relative `data/...` paths and crash
# with OSError if the directory doesn't exist. docker-compose.yml also bind-mounts
# ./data here; this mkdir just makes the image self-sufficient without the mount too.
RUN mkdir -p data

CMD ["python", "-m", "src.orchestrator.run_pipeline"]
