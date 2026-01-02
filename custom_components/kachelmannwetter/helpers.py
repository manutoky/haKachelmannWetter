"""Helpers to normalize Kachelmann API responses to canonical keys."""
from __future__ import annotations

from typing import Any

WEATHER_SYMBOL_DICT = {
    "cloudy": "cloudy",
    "fog": "fog",
    "freezingrain": "exceptional",
    "overcast": "cloudy",
    "partlycloudy": "partlycloudy",
    "partlycloudy2": "partlycloudy",
    "rain": "rainy",
    "raindrizzle": "rainy",
    "rainheavy": "pouring",
    "severethunderstorm": "lightning-rainy",
    "showers": "rainy",
    "showersheavy": "rainy",
    "snow": "snowy",
    "snowheavy": "snowy",
    "snowrain": "snowy-rainy",
    "snowrainshowers": "snowy-rainy",
    "snowshowers": "snowy",
    "snowshowersheavy": "snowy",
    "sunshine": "sunny",
    "thunderstorm": "lightning-rainy",
    "wind": "windy",
}

def _first(*keys: str, data: dict[str, Any]):
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    return None

def safeget(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            return None
    return dct

def normalize_current(data: dict[str, Any]) -> dict[str, Any]:
    if not data:
        return {}

    out: dict[str, Any] = {}

    out["temperature"] = safeget(data, "data", "temp", "value")
    out["humidity"] = safeget(data, "data", "humidityRelative", "value")
    out["pressure"] = safeget(data, "data", "pressureMsl", "value")
    out["wind_speed"] = safeget(data, "data", "windSpeed", "value")
    out["wind_gust"] = safeget(data, "data", "windGust", "value")
    out["wind_bearing"] = safeget(data, "data", "windDirection", "value")
    out["precipitation_1h"] = safeget(data, "data", "prec1h", "value")
    # out["precipitation_24h"] = _first("precipitation_24h", "rain_24h", "precip_24h", data=data)
    # out["visibility"] = _first("visibility", "vis", data=data)
    out["condition"] = WEATHER_SYMBOL_DICT.get(safeget(data, "data", "weatherSymbol", "value"))
    # out["timestamp"] = _first("timestamp", "time", "date", data=data)
    # out["station"] = _first("station", "station_id", "stationName", data=data) 

    return out

