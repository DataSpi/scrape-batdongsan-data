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

CMD ["python", "-m", "src.orchestrator.run_pipeline"]
