# End-to-End Weather ETL Pipeline

A complete ETL pipeline built with Python, PostgreSQL, Pandas, SQLAlchemy, and Docker.

The project extracts current weather data from the Open-Meteo API, stores raw JSON snapshots, transforms and validates the data, loads valid observations into PostgreSQL, and provides SQL analytics queries.

## Architecture

Open-Meteo API
      |
      v
Extraction
      |
      v
Raw JSON Storage
      |
      v
Pandas Transformation
      |
      v
Data Validation
      |
      v
PostgreSQL
      |
      v
SQL Analytics

The full environment runs with Docker Compose.
Tech Stack
- Python 3.11
- Pandas
- Requests
- SQLAlchemy
- PostgreSQL 17
- Docker
- Docker Compose
- pytest
- python-dotenv
- SQL
Data Source
The pipeline consumes current weather data from the Open-Meteo API.
Cities currently included:
- Agadir
- Casablanca
- Rabat
- Marrakesh
- Tangier
Collected fields include:
- Temperature
- Relative humidity
- Wind speed
- Weather code
- Observation timestamp
- Latitude
- Longitude
ETL Flow
Extract
The pipeline sends HTTP requests to Open-Meteo and retrieves current weather observations for the configured cities.
Raw Data Storage
Each extraction is stored as a timestamped JSON file under:
data/raw/

This preserves the original extracted data for traceability and possible reprocessing.
Transform
The raw records are converted into a Pandas DataFrame.
The transformation layer:
- Renames fields
- Converts numeric values
- Parses timestamps
- Normalizes text fields
- Removes exact duplicate rows
Validate
Before loading into PostgreSQL, each row is checked against data-quality rules.
Validation includes:
- Required field checks
- Latitude between -90 and 90
- Longitude between -180 and 180
- Humidity between 0 and 100
- Temperature between -100°C and 70°C
- Wind speed greater than or equal to 0
- Weather code greater than or equal to 0
- Duplicate detection using city + observed_at
Invalid rows are separated from valid rows instead of being silently discarded.
Load
Validated rows are inserted into PostgreSQL using SQLAlchemy.
The destination table is:
weather_observations

Idempotency
The pipeline is designed to be safe to run multiple times.
The business key is:
(city, observed_at)

PostgreSQL enforces this through a unique constraint.
The loader uses:
ON CONFLICT DO NOTHING

As a result, running the pipeline multiple times with the same observations does not create duplicate rows.
Database Schema
Main columns in weather_observations:
id
city
country
latitude
longitude
temperature_c
humidity
wind_speed
weather_code
observed_at
ingested_at

The database also includes constraints for data integrity.
SQL Analytics
Analytics queries are available in:
sql/analysis.sql

Examples include:
- Observation count by city
- Average temperature by city
- Minimum and maximum temperature
- Average humidity
- Average wind speed
- Latest observation per city
- Overall weather summary
- Window-function ranking
- Time-based temperature aggregation
Testing
The project uses pytest for automated testing.
The current test suite contains 21 tests covering transformation and validation behavior.
Run the test suite with:
docker compose run --rm etl python -m pytest -v

Running the Project
1. Clone the repository
git clone <repository-url>
cd etl-weather-pipeline

2. Create the environment file
Copy:
.env.example

to:
.env

3. Build the Docker images
docker compose build

4. Start PostgreSQL
docker compose up -d postgres

Check its status:
docker compose ps

PostgreSQL should appear as healthy.
5. Create the database schema
docker compose run --rm etl python -m src.db_schema

6. Run the automated tests
docker compose run --rm etl python -m pytest -v

7. Run the ETL pipeline
docker compose run --rm etl python -m src.pipeline

The pipeline will:
Extract
  ↓
Save raw JSON
  ↓
Transform
  ↓
Validate
  ↓
Load into PostgreSQL

8. Inspect the database
Open PostgreSQL:
docker compose exec postgres psql -U etl_user -d weather_db

Example query:
SELECT *
FROM weather_observations
ORDER BY observed_at DESC;

Exit PostgreSQL with:
\q

Project Structure
etl-weather-pipeline/
├── src/
│   ├── config.py
│   ├── db_schema.py
│   ├── extract.py
│   ├── load.py
│   ├── logging_config.py
│   ├── pipeline.py
│   ├── raw_storage.py
│   ├── transform.py
│   └── validate.py
│
├── tests/
│   ├── test_transform.py
│   └── test_validate.py
│
├── sql/
│   ├── schema.sql
│   └── analysis.sql
│
├── data/
│   └── raw/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md

Reliability Features
The project includes:
- Raw data preservation
- Data validation before loading
- PostgreSQL integrity constraints
- Idempotent database inserts
- Transaction-based loading
- Centralized logging
- Explicit error propagation
- PostgreSQL health checks
- Automated pytest tests
- Dockerized execution
Future Improvements
Possible future extensions include:
- Apache Airflow orchestration
- Scheduled execution
- Google Cloud deployment
- BigQuery integration
- CI/CD pipeline
- Monitoring and alerting
- Historical weather ingestion at larger scale

  
Author
Mohamed Amine Daghouri
