"""Validate transformed weather rows and separate rejects."""

import logging

import pandas as pd

from src.transform import (
    COLUMNS,
    latest_raw_file,
    load_raw_file,
    transform_weather_data,
)

logger = logging.getLogger(__name__)


def validate_weather_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return valid rows and rejected rows with validation_errors."""
    missing_columns = [column for column in COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"DataFrame is missing columns: {', '.join(missing_columns)}")

    frame = df.copy()
    errors = {index: [] for index in frame.index}

    def flag(mask: pd.Series, message: str) -> None:
        matched = mask.fillna(False).astype(bool)
        for index in frame.index[matched]:
            errors[index].append(message)

    city = frame["city"].astype("string")
    country = frame["country"].astype("string")
    flag(city.isna() | (city.str.strip() == ""), "city is missing")
    flag(country.isna() | (country.str.strip() == ""), "country is missing")

    for column in (
        "latitude",
        "longitude",
        "temperature_c",
        "humidity",
        "wind_speed",
        "weather_code",
        "observed_at",
    ):
        flag(frame[column].isna(), f"{column} is missing")

    latitude = frame["latitude"]
    longitude = frame["longitude"]
    temperature = frame["temperature_c"]
    humidity = frame["humidity"]
    wind_speed = frame["wind_speed"]
    weather_code = frame["weather_code"]

    flag(
        latitude.notna() & ((latitude < -90) | (latitude > 90)),
        "latitude must be between -90 and 90",
    )
    flag(
        longitude.notna() & ((longitude < -180) | (longitude > 180)),
        "longitude must be between -180 and 180",
    )
    flag(
        temperature.notna() & ((temperature < -100) | (temperature > 70)),
        "temperature_c must be between -100 and 70",
    )
    flag(
        humidity.notna() & ((humidity < 0) | (humidity > 100)),
        "humidity must be between 0 and 100",
    )
    flag(wind_speed.notna() & (wind_speed < 0), "wind_speed must be >= 0")
    flag(weather_code.notna() & (weather_code < 0), "weather_code must be >= 0")

    key_ready = city.notna() & (city.str.strip() != "") & frame["observed_at"].notna()
    duplicates = frame.duplicated(subset=["city", "observed_at"], keep="first")
    flag(duplicates & key_ready, "duplicate city + observed_at observation")

    failed = pd.Series(
        [bool(errors[index]) for index in frame.index],
        index=frame.index,
    )
    valid_df = frame.loc[~failed].copy()
    rejected_df = frame.loc[failed].copy()
    rejected_df["validation_errors"] = [
        "; ".join(errors[index]) for index in rejected_df.index
    ]

    logger.info(
        "Validation completed: %s total, %s valid, %s rejected",
        len(frame),
        len(valid_df),
        len(rejected_df),
    )
    if len(rejected_df):
        logger.warning("Rejected %s rows that failed data-quality checks", len(rejected_df))
    return valid_df, rejected_df


def _invalid_demo_frame() -> pd.DataFrame:
    """In-memory rows used only to show that validation catches bad data."""
    observed_at = "2026-09-27T12:30:00+00:00"
    demo = pd.DataFrame(
        [
            {
                "city": "Agadir",
                "country": "Morocco",
                "latitude": 30.4375,
                "longitude": -9.625,
                "temperature_c": 24.3,
                "humidity": 79,
                "wind_speed": 10.0,
                "weather_code": 3,
                "observed_at": observed_at,
            },
            {
                "city": "",
                "country": "Morocco",
                "latitude": 120,
                "longitude": -9.625,
                "temperature_c": 24.3,
                "humidity": 150,
                "wind_speed": 10.0,
                "weather_code": 3,
                "observed_at": observed_at,
            },
            {
                "city": "Agadir",
                "country": "Morocco",
                "latitude": 30.4375,
                "longitude": -9.625,
                "temperature_c": 25.0,
                "humidity": 80,
                "wind_speed": 11.0,
                "weather_code": 1,
                "observed_at": observed_at,
            },
        ]
    )
    demo["observed_at"] = pd.to_datetime(demo["observed_at"], utc=True)
    return demo


def _print_result(valid_df: pd.DataFrame, rejected_df: pd.DataFrame) -> None:
    print(f"Total rows: {len(valid_df) + len(rejected_df)}")
    print(f"Valid rows: {len(valid_df)}")
    print(f"Rejected rows: {len(rejected_df)}")
    print()
    print("Valid rows:")
    print(valid_df.to_string() if not valid_df.empty else "(none)")
    print()
    print("Rejected rows:")
    print(rejected_df.to_string() if not rejected_df.empty else "(none)")


def main() -> None:
    from src.logging_config import configure_logging

    configure_logging()
    path = latest_raw_file()
    logger.info("Validating latest raw file %s", path.name)
    frame = transform_weather_data(load_raw_file(path))
    valid_df, rejected_df = validate_weather_data(frame)
    _print_result(valid_df, rejected_df)

    print()
    print("Demonstration with intentionally invalid rows:")
    demo_valid, demo_rejected = validate_weather_data(_invalid_demo_frame())
    _print_result(demo_valid, demo_rejected)


if __name__ == "__main__":
    main()
