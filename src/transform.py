"""Transform raw weather records into a typed Pandas DataFrame."""

import json
import logging
from pathlib import Path

import pandas as pd

from src.raw_storage import RAW_DIR

logger = logging.getLogger(__name__)

COLUMNS = [
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

RENAME_COLUMNS = {
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "humidity",
    "wind_speed_10m": "wind_speed",
    "time": "observed_at",
}

NUMERIC_COLUMNS = [
    "latitude",
    "longitude",
    "temperature_c",
    "humidity",
    "wind_speed",
]


def load_raw_file(path: Path) -> list[dict]:
    """Read the records list from one raw extraction file."""
    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        logger.error("Failed to read raw weather file %s: %s", path, exc)
        raise
    except json.JSONDecodeError as exc:
        logger.error("Raw weather file %s is not valid JSON: %s", path, exc)
        raise

    records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError(f"Raw weather file {path} must contain a list of record objects")

    logger.info("Loaded %s records from %s", len(records), path)
    return records


def transform_weather_data(records: list[dict]) -> pd.DataFrame:
    """Rename, type, and de-duplicate raw weather records."""
    if not isinstance(records, list):
        logger.error("Transformation expected a list of records")
        raise TypeError("records must be a list")

    frame = pd.DataFrame(records)
    frame = frame.rename(columns=RENAME_COLUMNS)
    frame = frame.reindex(columns=COLUMNS)

    for column in ("city", "country"):
        frame[column] = frame[column].astype("string").str.strip()

    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["weather_code"] = pd.to_numeric(frame["weather_code"], errors="coerce").astype("Int64")
    frame["observed_at"] = pd.to_datetime(frame["observed_at"], errors="coerce", utc=True)

    before = len(frame)
    frame = frame.drop_duplicates().reset_index(drop=True)
    removed = before - len(frame)
    if removed:
        logger.info("Removed %s exact duplicate rows", removed)

    logger.info("Transformed %s weather rows", len(frame))
    return frame


def latest_raw_file(raw_dir: Path = RAW_DIR) -> Path:
    """Return the newest weather_*.json file in data/raw."""
    files = sorted(Path(raw_dir).glob("weather_*.json"))
    if not files:
        raise FileNotFoundError(f"No raw weather files found in {raw_dir}")
    return files[-1]


def main() -> None:
    from src.logging_config import configure_logging

    configure_logging()
    path = latest_raw_file()
    logger.info("Using latest raw file %s", path.name)
    records = load_raw_file(path)
    frame = transform_weather_data(records)

    print("Transformed weather data:")
    print(frame.to_string())
    print()
    print(f"Rows: {frame.shape[0]}")
    print(f"Columns: {frame.shape[1]}")
    print()
    print("Dtypes:")
    print(frame.dtypes.to_string())


if __name__ == "__main__":
    main()
