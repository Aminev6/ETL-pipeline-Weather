"""Retrieve current weather observations from the Open-Meteo API."""

import logging
from typing import TypedDict

import requests

from src.raw_storage import PROJECT_ROOT, save_raw_data

logger = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 10

CURRENT_VARIABLES = (
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "weather_code",
)

# City-center coordinates. Open-Meteo identifies locations by latitude and longitude.
LOCATIONS = (
    {"city": "Agadir", "country": "Morocco", "latitude": 30.4278, "longitude": -9.5981},
    {"city": "Casablanca", "country": "Morocco", "latitude": 33.5731, "longitude": -7.5898},
    {"city": "Rabat", "country": "Morocco", "latitude": 34.0209, "longitude": -6.8416},
    {"city": "Marrakesh", "country": "Morocco", "latitude": 31.6295, "longitude": -7.9811},
    {"city": "Tangier", "country": "Morocco", "latitude": 35.7595, "longitude": -5.8340},
)


class WeatherObservation(TypedDict):
    """One current observation, still using Open-Meteo field names."""

    city: str
    country: str
    latitude: float
    longitude: float
    temperature_2m: float
    relative_humidity_2m: float
    wind_speed_10m: float
    weather_code: int
    time: str


def extract_weather_data() -> list[WeatherObservation]:
    """Request current weather for every configured location."""
    observations: list[WeatherObservation] = []
    for location in LOCATIONS:
        observations.append(_extract_location(location))
    logger.info("Extracted weather data for %s locations", len(observations))
    return observations


def _extract_location(location: dict) -> WeatherObservation:
    city = location["city"]
    country = location["country"]
    logger.info("Requesting current weather for %s, %s", city, country)

    try:
        response = requests.get(
            FORECAST_URL,
            params=_request_params(location),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout:
        logger.error(
            "Open-Meteo request timed out for %s, %s after %s seconds",
            city,
            country,
            REQUEST_TIMEOUT_SECONDS,
        )
        raise
    except requests.ConnectionError:
        logger.error("Open-Meteo connection failed for %s, %s", city, country)
        raise
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        logger.error("Open-Meteo HTTP error for %s, %s: status %s", city, country, status)
        raise
    except requests.JSONDecodeError:
        logger.error("Open-Meteo returned invalid JSON for %s, %s", city, country)
        raise
    except requests.RequestException:
        logger.error("Open-Meteo request failed for %s, %s", city, country)
        raise

    try:
        observation = _observation_from_payload(location, payload)
    except ValueError as exc:
        logger.error(
            "Open-Meteo response for %s, %s could not be read: %s",
            city,
            country,
            exc,
        )
        raise
    logger.info("Received current weather for %s at %s", city, observation["time"])
    return observation


def _request_params(location: dict) -> dict:
    return {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": ",".join(CURRENT_VARIABLES),
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "timezone": "UTC",
    }


def _observation_from_payload(location: dict, payload: dict) -> WeatherObservation:
    current = payload.get("current")
    if not isinstance(current, dict):
        raise ValueError(
            f"Open-Meteo response for {location['city']} has no current observation"
        )

    missing = [
        name
        for name in ("time", *CURRENT_VARIABLES)
        if current.get(name) is None
    ]
    if payload.get("latitude") is None or payload.get("longitude") is None:
        missing.extend(
            name for name in ("latitude", "longitude") if payload.get(name) is None
        )
    if missing:
        raise ValueError(
            f"Open-Meteo response for {location['city']} is missing: {', '.join(missing)}"
        )

    return {
        "city": location["city"],
        "country": location["country"],
        "latitude": payload["latitude"],
        "longitude": payload["longitude"],
        "temperature_2m": current["temperature_2m"],
        "relative_humidity_2m": current["relative_humidity_2m"],
        "wind_speed_10m": current["wind_speed_10m"],
        "weather_code": current["weather_code"],
        "time": current["time"],
    }


def main() -> None:
    from src.logging_config import configure_logging

    configure_logging()
    observations = extract_weather_data()
    path = save_raw_data(observations)
    print(f"Extraction successful: {len(observations)} cities")
    print(f"Raw data saved to: {path.relative_to(PROJECT_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
