"""Load database settings from the environment and connect with SQLAlchemy."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine

logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Config:
    """Database settings read from environment variables."""

    def __init__(self) -> None:
        self.db_host = _required_env("DB_HOST")
        self.db_port = int(_required_env("DB_PORT"))
        self.db_name = _required_env("DB_NAME")
        self.db_user = _required_env("DB_USER")
        self.db_password = _required_env("DB_PASSWORD")

    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


config = Config()
engine: Engine = create_engine(config.database_url())


def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine."""
    return engine


def verify_connection() -> None:
    """Check that PostgreSQL accepts a connection."""
    logger.info(
        "Checking PostgreSQL connection to %s:%s/%s as %s",
        config.db_host,
        config.db_port,
        config.db_name,
        config.db_user,
    )
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar_one()
    except Exception:
        logger.exception(
            "PostgreSQL connection failed for %s:%s/%s",
            config.db_host,
            config.db_port,
            config.db_name,
        )
        raise
    if result != 1:
        logger.error("Unexpected connection check result: %s", result)
        raise RuntimeError(f"Unexpected connection check result: {result}")
    message = (
        "PostgreSQL connection successful: "
        f"{config.db_user}@{config.db_host}:{config.db_port}/{config.db_name}"
    )
    logger.info(message)
    print(message)


if __name__ == "__main__":
    from src.logging_config import configure_logging

    configure_logging()
    verify_connection()
