"""A small client for the Open-Meteo forecast API.

Open-Meteo is free and needs no API key, which is why it's the "real"
data source in an otherwise synthetic world: every farm's weather is a
genuine forecast for its real latitude/longitude.

Following the same testability pattern as graph.py in Phase 00: the part
that makes an HTTP call (`_fetch_raw`) is separated from the part that
parses the response (`_parse_forecast`), so tests can feed the parser a
canned JSON payload and never touch the network. A small on-disk cache
keeps repeated runs (and repeated pytest runs) from re-fetching the same
forecast, since the free API is a shared, polite-use resource.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_DIR = Path(".cache/weather")
CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours — forecasts don't change that fast


@dataclass(frozen=True)
class DailyWeather:
    date: str
    temperature_max_c: float
    temperature_min_c: float
    precipitation_mm: float


@dataclass(frozen=True)
class Forecast:
    latitude: float
    longitude: float
    days: tuple[DailyWeather, ...]


def _cache_path(latitude: float, longitude: float) -> Path:
    # Round coordinates so nearby farms sharing a region share a cache
    # entry too, instead of each farm re-fetching an almost-identical forecast.
    key = f"{round(latitude, 2)}_{round(longitude, 2)}.json"
    return CACHE_DIR / key


def _fetch_raw(latitude: float, longitude: float, timeout: float = 10.0) -> dict:
    """The only function in this module that touches the network."""
    response = httpx.get(
        OPEN_METEO_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
            "forecast_days": 7,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _parse_forecast(latitude: float, longitude: float, payload: dict) -> Forecast:
    """Pure function: JSON in, typed Forecast out. No network here, so this
    is what tests/test_weather.py exercises directly.
    """
    daily = payload["daily"]
    days = tuple(
        DailyWeather(
            date=daily["time"][i],
            temperature_max_c=daily["temperature_2m_max"][i],
            temperature_min_c=daily["temperature_2m_min"][i],
            precipitation_mm=daily["precipitation_sum"][i],
        )
        for i in range(len(daily["time"]))
    )
    return Forecast(latitude=latitude, longitude=longitude, days=days)


def get_forecast(latitude: float, longitude: float, use_cache: bool = True) -> Forecast:
    """Fetch (or reuse a cached) 7-day forecast for a location."""
    cache_file = _cache_path(latitude, longitude)

    if use_cache and cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < CACHE_TTL_SECONDS:
            payload = json.loads(cache_file.read_text())
            return _parse_forecast(latitude, longitude, payload)

    payload = _fetch_raw(latitude, longitude)

    if use_cache:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(payload))

    return _parse_forecast(latitude, longitude, payload)
