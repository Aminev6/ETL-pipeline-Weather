"""Apply the versioned PostgreSQL schema."""

import logging
from pathlib import Path

from sqlalchemy import inspect, text

from src.config import engine

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
TABLE_NAME = "weather_observations"


def apply_schema() -> None:
    """Read sql/schema.sql and apply it in one transaction."""
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to read schema file %s: %s", SCHEMA_PATH, exc)
        raise

    try:
        with engine.begin() as connection:
            connection.execute(text(schema_sql))
    except Exception as exc:
        logger.error("Failed to apply database schema: %s", exc)
        raise

    logger.info("Database schema applied successfully")


def list_table_columns(table_name: str = TABLE_NAME) -> list[str]:
    """Return column names when the table exists."""
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        raise RuntimeError(f"Table {table_name} does not exist")
    return [column["name"] for column in inspector.get_columns(table_name)]


def main() -> None:
    from src.logging_config import configure_logging

    configure_logging()
    apply_schema()
    columns = list_table_columns()
    print("Database schema applied successfully.")
    print(f"Table {TABLE_NAME} is ready.")
    for column in columns:
        print(column)


if __name__ == "__main__":
    main()
