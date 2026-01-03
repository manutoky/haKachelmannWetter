"""Helpers to normalize Kachelmann API responses to canonical keys."""
from __future__ import annotations

from typing import Any
from datetime import datetime, date

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

def normalize_forecasts(data: dict[str, Any]) -> dict[str, Any]:
    # This expecting data in 6h steps from /advanced/6h endpoint
    # We want to provide daily forecasts from this
    if not data:
        return {}

    out: dict[str, Any] = {}
    out["daily"] = []
    daily_data: dict[date, dict[str, Any]] = {}
    
    for entry in data.get("data", []):
        
        date_key = datetime.fromisoformat(entry["dateTime"]).date()
        timeofday = datetime.fromisoformat(entry["dateTime"]).time()
        if date_key not in daily_data:
            daily_data[date_key] = {
                "cloud_coverage": [],
                "condition": set(),
                "humidity": [],
                "native_apparent_temperature": [],
                "native_dew_point": [],
                "native_precipitation": [],
                "native_pressure": [],
                "native_temperature": [],
                "native_templow": [],
                "native_wind_gust_speed": [],
                "native_wind_speed": [],
                "precipitation_probability": [],
                "uv_index": [],
                "wind_bearing": [],
                "timeofday": timeofday,
            }
            
        
        daily_data[date_key]["cloud_coverage"].append(entry.get("cloudCoverage"))
        daily_data[date_key]["condition"].add(WEATHER_SYMBOL_DICT.get(entry.get("weatherSymbol")))
        daily_data[date_key]["humidity"].append(entry.get("humidityRelative"))
        daily_data[date_key]["native_dew_point"].append(entry.get("dewpoint"))
        daily_data[date_key]["native_precipitation"].append(entry.get("prec6h", 0))
        daily_data[date_key]["native_pressure"].append(entry.get("pressureMsl"))
        daily_data[date_key]["native_temperature"].append(entry["tempMax6h"])
        daily_data[date_key]["native_templow"].append(entry["tempMin6h"])
        daily_data[date_key]["native_wind_gust_speed"].append(entry.get("windGust"))
        daily_data[date_key]["native_wind_speed"].append(entry.get("windSpeed"))
        #daily_data[date_key]["precipitation_probability"].append(entry.get("precProb"))
        #daily_data[date_key]["uv_index"].append(entry.get("uvIndex"))
        daily_data[date_key]["wind_bearing"].append(entry.get("windDirection"))

    for date_key, entry in daily_data.items():
        forecast = {
            "datetime": date_key.isoformat(),
            "condition": max(entry["condition"], key=lambda x: list(WEATHER_SYMBOL_DICT.values()).index(x)) if entry["condition"] else None,
            "cloudCoverage": sum(entry["cloud_coverage"])/len(entry["cloud_coverage"]) if entry["cloud_coverage"] else None,
            "humidity": sum(entry["humidity"])/len(entry["humidity"]) if entry["humidity"] else None,
            "native_dew_point": sum(entry["native_dew_point"])/len(entry["native_dew_point"]) if entry["native_dew_point"] else None,
            "native_precipitation": sum(entry["native_precipitation"]) if entry["native_precipitation"] else 0,
            "native_pressure": sum(entry["native_pressure"])/len(entry["native_pressure"]) if entry["native_pressure"] else None,
            "native_temperature": max(entry["native_temperature"]) if entry["native_temperature"] else None,
            "native_templow": min(entry["native_templow"]) if entry["native_templow"] else None,
            "native_wind_gust_speed": max(entry["native_wind_gust_speed"]) if entry["native_wind_gust_speed"] else None,
            "native_wind_speed": max(entry["native_wind_speed"]) if entry["native_wind_speed"] else None,
            "precipitation_probability": max(entry["precipitation_probability"]) if entry["precipitation_probability"] else None,
            "wind_bearing": int(sum(entry["wind_bearing"])/len(entry["wind_bearing"])) if entry["wind_bearing"] else None,
            # Add more fields as needed
        }
        out["daily"].append(forecast)
  
    return out