"""Orchestrate the weather ETL pipeline."""

import logging

from src.extract import extract_weather_data
from src.load import load_weather_data
from src.logging_config import configure_logging
from src.raw_storage import PROJECT_ROOT, save_raw_data
from src.transform import transform_weather_data
from src.validate import validate_weather_data

logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    """Extract, archive, transform, validate, and load current weather."""
    try:
        logger.info("Starting extraction")
        records = extract_weather_data()
    except Exception:
        logger.exception("Extraction stage failed")
        raise

    try:
        logger.info("Saving raw data")
        raw_path = save_raw_data(records)
    except Exception:
        logger.exception("Raw persistence stage failed")
        raise
    relative_path = raw_path.relative_to(PROJECT_ROOT).as_posix()

    try:
        logger.info("Transforming data")
        frame = transform_weather_data(records)
    except Exception:
        logger.exception("Transformation stage failed")
        raise

    try:
        logger.info("Validating data")
        valid_df, rejected_df = validate_weather_data(frame)
    except Exception:
        logger.exception("Validation stage failed")
        raise

    if valid_df.empty:
        logger.info("No valid rows to load")
        inserted = 0
        skipped = 0
    else:
        try:
            logger.info("Loading valid rows")
            stats = load_weather_data(valid_df)
        except Exception:
            logger.exception("Loading stage failed")
            raise
        inserted = stats.inserted
        skipped = stats.skipped

    logger.info("ETL pipeline completed successfully")
    print("ETL pipeline completed successfully")
    print(f"Extracted rows: {len(records)}")
    print(f"Raw file: {relative_path}")
    print(f"Transformed rows: {len(frame)}")
    print(f"Valid rows: {len(valid_df)}")
    print(f"Rejected rows: {len(rejected_df)}")
    print(f"Inserted rows: {inserted}")
    print(f"Skipped existing rows: {skipped}")


if __name__ == "__main__":
    configure_logging()
    run_pipeline()
