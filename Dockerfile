FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY tests ./tests
COPY sql ./sql
COPY data/raw/.gitkeep ./data/raw/.gitkeep

# The pipeline is a one-shot command, not a long-running service:
# docker compose run --rm etl python -m src.pipeline
CMD ["python", "-c", "print('ETL image ready')"]
