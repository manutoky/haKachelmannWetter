"""DataUpdateCoordinator for KachelmannWetter."""
from __future__ import annotations

from datetime import timedelta
from logging import Logger, getLogger

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.event import async_call_later

from .exceptions import RateLimitError, InvalidAuth

from .client import KachelmannClient
from .helpers import normalize_current, normalize_forecasts
from .const import DEFAULT_UPDATE_INTERVAL

_LOGGER: Logger = getLogger(__package__)


class KachelmannDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        latitude: float,
        longitude: float,
        update_interval_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.client = KachelmannClient(hass, api_key)
        _LOGGER.debug("Coordinator initialized for %s,%s", latitude, longitude)
        if update_interval_seconds is None:
            update_interval_seconds = DEFAULT_UPDATE_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name="kachelmannwetter",
            update_interval=timedelta(seconds=update_interval_seconds),
        )

    async def _async_update_data(self) -> dict:
        _LOGGER.debug("Starting data update for %s,%s", self.latitude, self.longitude)
        try:
            current = await self.client.async_get_current(self.latitude, self.longitude)
            forecast = await self.client.async_get_forecast(self.latitude, self.longitude)
            # normalize current condition fields for consistent entity mapping
            normalized_current = normalize_current(current or {})
            normalized_forecasts = normalize_forecasts(forecast or {})
            return {"current": normalized_current, "forecast": normalized_forecasts}
        except RateLimitError as err:
            retry = getattr(err, "retry_after", None)
            _LOGGER.warning("Rate limited by Kachelmann API, retry after %s seconds", retry)
            if retry:
                # schedule a refresh after retry seconds
                async_call_later(self.hass, retry, lambda _now: self.async_request_refresh())
            raise UpdateFailed("Rate limited by Kachelmann API") from err
        except InvalidAuth as err:
            _LOGGER.error("Invalid API key for KachelmannWetter: %s", err)
            raise
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
