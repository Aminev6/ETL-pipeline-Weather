"""Load validated weather rows into PostgreSQL."""

import logging
from dataclasses import dataclass

import pandas as pd
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, MetaData, String, Table, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.config import engine
from src.transform import latest_raw_file, load_raw_file, transform_weather_data
from src.validate import validate_weather_data

logger = logging.getLogger(__name__)

weather_observations = Table(
    "weather_observations",
    MetaData(),
    Column("id", BigInteger, primary_key=True),
    Column("city", String),
    Column("country", String),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("temperature_c", Float),
    Column("humidity", Integer),
    Column("wind_speed", Float),
    Column("weather_code", Integer),
    Column("observed_at", DateTime(timezone=True)),
)

LOAD_COLUMNS = [
    "city",
    "country",
    "latitude",
    "longitude",
    "temperature_c",
    "humidity",
    "wind_speed",
    "weather_code",
    "observed_at",
]

COUNT_SQL = text("SELECT COUNT(*) FROM weather_observations")

DUPLICATE_SQL = text(
    """
    SELECT city, observed_at, COUNT(*) AS row_count
    FROM weather_observations
    GROUP BY city, observed_at
    HAVING COUNT(*) > 1
    """
)

PREVIEW_SQL = text(
    """
    SELECT
        id,
        city,
        temperature_c,
        humidity,
        observed_at,
        ingested_at
    FROM weather_observations
    ORDER BY id
    """
)


@dataclass(frozen=True)
class LoadResult:
    """How many validated rows were received, inserted, or already stored."""

    received: int
    inserted: int
    skipped: int


def load_weather_data(df: pd.DataFrame) -> LoadResult:
    """Insert validated rows. Existing city + observed_at rows are left unchanged."""
    missing_columns = [column for column in LOAD_COLUMNS if column not in df.columns]
    if missing_columns:
        logger.error("Load received a DataFrame missing columns: %s", ", ".join(missing_columns))
        raise ValueError(f"DataFrame is missing columns: {', '.join(missing_columns)}")

    records = _records(df)
    received = len(records)
    if not records:
        result = LoadResult(received=0, inserted=0, skipped=0)
        logger.info(
            "Rows received: %s; inserted rows: %s; skipped existing rows: %s",
            result.received,
            result.inserted,
            result.skipped,
        )
        return result

    statement = (
        pg_insert(weather_observations)
        .values(records)
        .on_conflict_do_nothing(constraint="uq_weather_observations_city_observed_at")
        .returning(weather_observations.c.id)
    )
    try:
        with engine.begin() as connection:
            inserted_ids = connection.execute(statement).scalars().all()
    except IntegrityError as exc:
        logger.error("Load failed because a database constraint was violated: %s", exc.orig)
        raise
    except SQLAlchemyError as exc:
        logger.error("Failed to load weather observations: %s", exc)
        raise

    result = LoadResult(
        received=received,
        inserted=len(inserted_ids),
        skipped=received - len(inserted_ids),
    )
    logger.info(
        "Rows received: %s; inserted rows: %s; skipped existing rows: %s",
        result.received,
        result.inserted,
        result.skipped,
    )
    return result


def fetch_observations() -> list[dict]:
    """Return loaded rows for a short verification preview."""
    with engine.connect() as connection:
        rows = connection.execute(PREVIEW_SQL).mappings().all()
    return [dict(row) for row in rows]


def _records(df: pd.DataFrame) -> list[dict]:
    records = []
    for row in df.loc[:, LOAD_COLUMNS].itertuples(index=False):
        observed_at = row.observed_at
        if isinstance(observed_at, pd.Timestamp):
            observed_at = observed_at.to_pydatetime()
        records.append(
            {
                "city": str(row.city),
                "country": str(row.country),
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "temperature_c": float(row.temperature_c),
                "humidity": int(row.humidity),
                "wind_speed": float(row.wind_speed),
                "weather_code": int(row.weather_code),
                "observed_at": observed_at,
            }
        )
    return records


def _print_preview(rows: list[dict]) -> None:
    print(
        f"{'id':<6} {'city':<12} {'temperature_c':<14} "
        f"{'humidity':<10} {'observed_at':<28} ingested_at"
    )
    for row in rows:
        print(
            f"{row['id']:<6} {row['city']:<12} {row['temperature_c']:<14} "
            f"{row['humidity']:<10} {row['observed_at']!s:<28} {row['ingested_at']}"
        )


def main() -> None:
    from src.logging_config import configure_logging

    configure_logging()
    path = latest_raw_file()
    logger.info("Loading latest raw file %s", path.name)
    frame = transform_weather_data(load_raw_file(path))
    valid_df, _rejected_df = validate_weather_data(frame)
    print(f"Valid rows ready for loading: {len(valid_df)}")
    result = load_weather_data(valid_df)
    print(f"Rows received: {result.received}")
    print(f"Inserted rows: {result.inserted}")
    print(f"Skipped existing rows: {result.skipped}")
    print()
    print("weather_observations:")
    _print_preview(fetch_observations())
    print()
    with engine.connect() as connection:
        row_count = connection.execute(COUNT_SQL).scalar_one()
        duplicates = connection.execute(DUPLICATE_SQL).mappings().all()
    print(f"SELECT COUNT(*) FROM weather_observations: {row_count}")
    print("Duplicate city + observed_at groups:")
    if duplicates:
        for row in duplicates:
            print(f"{row['city']} {row['observed_at']} count={row['row_count']}")
    else:
        print("(none)")


if __name__ == "__main__":
    main()
