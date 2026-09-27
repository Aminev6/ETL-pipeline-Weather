# ETL Weather Pipeline

A compact end-to-end ETL project that will ingest weather observations from a REST API, store the raw JSON, clean and validate the data, load it into PostgreSQL, and query it with SQL. This repository currently contains the project skeleton, development configuration, and a local PostgreSQL service. The pipeline is not implemented yet.

## Planned technology stack

- Python
- requests
- Pandas
- SQLAlchemy
- PostgreSQL
- Docker / Docker Compose
- pytest
- python-dotenv
- Git

## Planned architecture

```
REST API
    ↓
Extract
    ↓
Raw JSON storage
    ↓
Transform / Clean
    ↓
Data Validation
    ↓
PostgreSQL
    ↓
SQL Analytics
```

Future Python modules, not created yet:

- `src/extract.py` — call the REST API and retrieve raw data
- `src/transform.py` — clean, normalize, and validate the extracted data
- `src/load.py` — load valid data into PostgreSQL
- `src/pipeline.py` — orchestrate the full ETL process

## Start PostgreSQL locally

PostgreSQL 17 runs in Docker Compose as the `postgres` service. The database is `weather_db`, the user is `etl_user`, and the host port is `5432`. Data is stored in the `postgres_data` volume, so it remains after the container stops.

From the project root:

```powershell
docker compose up -d postgres
```

Optional: copy `.env.example` to `.env` if you want to change the database name, user, password, or host port. Compose uses those values when `.env` is present, and the same defaults when it is not. `DB_HOST=localhost` is for clients on your machine. Inside Docker the database hostname is `postgres`.
