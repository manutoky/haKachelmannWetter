"""Weather platform for KachelmannWetter integration."""
from __future__ import annotations

from typing import Any
from logging import Logger, getLogger

from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME
from .helpers import WEATHER_SYMBOL_DICT

_LOGGER: Logger = getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Adding KachelmannWeather entity for entry %s", entry.entry_id)
    async_add_entities([KachelmannWeather(coordinator)])


class KachelmannWeather(CoordinatorEntity, WeatherEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = DEFAULT_NAME

    @property
    def supported_features(self) -> WeatherEntityFeature:
        return WeatherEntityFeature.FORECAST_DAILY

    @property
    def condition(self) -> str | None:
        current = (self.coordinator.data or {}).get("current") or {}
        cond = current.get("condition")
        if not cond:
            return None
        _LOGGER.debug("Condition = %s", cond)
        return cond

    @property
    def native_temperature(self) -> float | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("temperature")

    @property
    def native_temperature_unit(self) -> str | None:
        return "°C"

    @property
    def humidity(self) -> int | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("humidity")

    @property
    def native_pressure(self) -> int | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("pressure")

    @property
    def native_pressure_unit(self) -> str | None:
        return "hPa"

    @property
    def native_wind_speed(self) -> float | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("wind_speed")

    @property
    def native_wind_speed_unit(self) -> str | None:
        return "m/s"

    @property
    def native_wind_gust(self) -> float | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("wind_gust")

    @property
    def wind_bearing(self) -> int | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("wind_bearing")

    @property
    def attribution(self) -> str | None:
        return "Data provided by KachelmannWetter"

    async def async_forecast_daily(self) -> list[Forecast] | None:
        # This is using the 14day trend forecast endpoint
        forecasts: list[dict[str, Any]] = []
        data = (self.coordinator.data or {}).get("forecast") or {}
        return data.get("daily")