"""Tests for weather-row validation."""

import pandas as pd
import pytest

from src.transform import transform_weather_data
from src.validate import validate_weather_data


@pytest.fixture
def raw_record() -> dict:
    return {
        "city": "Agadir",
        "country": "Morocco",
        "latitude": 30.4375,
        "longitude": -9.625,
        "temperature_2m": 24.3,
        "relative_humidity_2m": 79,
        "wind_speed_10m": 10.0,
        "weather_code": 3,
        "time": "2026-09-27T12:30:00+00:00",
    }


@pytest.fixture
def valid_frame(raw_record) -> pd.DataFrame:
    return transform_weather_data([raw_record])


def test_normal_row_is_accepted(valid_frame):
    valid_df, rejected_df = validate_weather_data(valid_frame)

    assert len(valid_df) == 1
    assert len(rejected_df) == 0
    assert valid_df.iloc[0]["city"] == "Agadir"


def test_missing_city_is_rejected(valid_frame):
    frame = valid_frame.copy()
    frame.loc[0, "city"] = pd.NA

    valid_df, rejected_df = validate_weather_data(frame)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1
    assert "city is missing" in rejected_df.iloc[0]["validation_errors"]


def test_missing_observed_at_is_rejected(valid_frame):
    frame = valid_frame.copy()
    frame.loc[0, "observed_at"] = pd.NaT

    valid_df, rejected_df = validate_weather_data(frame)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1
    assert "observed_at is missing" in rejected_df.iloc[0]["validation_errors"]


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("humidity", 150, "humidity must be between 0 and 100"),
        ("humidity", -1, "humidity must be between 0 and 100"),
        ("latitude", 91, "latitude must be between -90 and 90"),
        ("latitude", -91, "latitude must be between -90 and 90"),
        ("longitude", 181, "longitude must be between -180 and 180"),
        ("longitude", -181, "longitude must be between -180 and 180"),
        ("wind_speed", -0.1, "wind_speed must be >= 0"),
        ("temperature_c", 71, "temperature_c must be between -100 and 70"),
        ("temperature_c", -101, "temperature_c must be between -100 and 70"),
        ("weather_code", -1, "weather_code must be >= 0"),
    ],
)
def test_out_of_range_value_is_rejected(valid_frame, column, value, message):
    frame = valid_frame.copy()
    frame.loc[0, column] = value

    valid_df, rejected_df = validate_weather_data(frame)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1
    assert message in rejected_df.iloc[0]["validation_errors"]


def test_duplicate_city_and_observed_at_keeps_first_row(raw_record):
    later = dict(raw_record)
    later["temperature_2m"] = 25.0
    frame = transform_weather_data([raw_record, later])

    valid_df, rejected_df = validate_weather_data(frame)

    assert len(valid_df) == 1
    assert len(rejected_df) == 1
    assert valid_df.iloc[0]["temperature_c"] == 24.3
    assert "duplicate city + observed_at observation" in rejected_df.iloc[0]["validation_errors"]


def test_row_with_multiple_problems_lists_every_error(valid_frame):
    frame = valid_frame.copy()
    frame.loc[0, "city"] = ""
    frame.loc[0, "latitude"] = 120
    frame.loc[0, "humidity"] = 150

    valid_df, rejected_df = validate_weather_data(frame)
    errors = rejected_df.iloc[0]["validation_errors"]

    assert len(valid_df) == 0
    assert len(rejected_df) == 1
    assert "city is missing" in errors
    assert "latitude must be between -90 and 90" in errors
    assert "humidity must be between 0 and 100" in errors
