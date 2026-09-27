"""Tests for raw-record transformation."""

import pandas as pd
import pytest

from src.transform import COLUMNS, transform_weather_data


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


def test_raw_records_become_dataframe_with_expected_columns(raw_record):
    frame = transform_weather_data([raw_record])

    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == COLUMNS
    assert len(frame) == 1


def test_raw_fields_are_renamed(raw_record):
    frame = transform_weather_data([raw_record])
    row = frame.iloc[0]

    assert row["temperature_c"] == 24.3
    assert row["humidity"] == 79
    assert row["wind_speed"] == 10.0
    assert row["weather_code"] == 3
    assert row["observed_at"] == pd.Timestamp("2026-09-27 12:30:00", tz="UTC")


def test_field_types_are_numeric_and_datetime(raw_record):
    frame = transform_weather_data([raw_record])

    for column in (
        "latitude",
        "longitude",
        "temperature_c",
        "humidity",
        "wind_speed",
        "weather_code",
    ):
        assert pd.api.types.is_numeric_dtype(frame[column])
    assert pd.api.types.is_datetime64_any_dtype(frame["observed_at"])


def test_city_and_country_whitespace_is_stripped(raw_record):
    raw_record["city"] = "  Agadir  "
    raw_record["country"] = " Morocco "

    frame = transform_weather_data([raw_record])

    assert frame.loc[0, "city"] == "Agadir"
    assert frame.loc[0, "country"] == "Morocco"


def test_malformed_numeric_values_become_missing(raw_record):
    raw_record["latitude"] = "north"
    raw_record["temperature_2m"] = "hot"
    raw_record["relative_humidity_2m"] = "damp"
    raw_record["wind_speed_10m"] = "fast"
    raw_record["weather_code"] = "cloudy"

    frame = transform_weather_data([raw_record])

    assert len(frame) == 1
    assert pd.isna(frame.loc[0, "latitude"])
    assert pd.isna(frame.loc[0, "temperature_c"])
    assert pd.isna(frame.loc[0, "humidity"])
    assert pd.isna(frame.loc[0, "wind_speed"])
    assert pd.isna(frame.loc[0, "weather_code"])


def test_exact_duplicate_rows_are_removed(raw_record):
    frame = transform_weather_data([raw_record, dict(raw_record)])

    assert len(frame) == 1
    assert frame.loc[0, "city"] == "Agadir"
