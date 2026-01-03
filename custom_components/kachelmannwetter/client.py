"""Thin async client for KachelmannWetter API."""
from __future__ import annotations

from typing import Any
import logging

from aiohttp import ClientResponseError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .exceptions import InvalidAuth, RateLimitError

_LOGGER = logging.getLogger(__name__)


class KachelmannClient:
    def __init__(self, hass, api_key: str) -> None:
        self._hass = hass
        self._session = async_get_clientsession(hass)
        self._api_key = api_key
        _LOGGER.debug("KachelmannClient initialized with api_key_provided=%s", bool(api_key))

    async def _get(self, url: str) -> dict[str, Any]:
        headers = {"X-API-Key": self._api_key}
        _LOGGER.debug("HTTP GET %s (api_key_provided=%s)", url, bool(self._api_key))
        resp = await self._session.get(url, headers=headers)
        # Handle common status codes explicitly
        if resp.status == 401:
            _LOGGER.error("Received 401 Unauthorized from Kachelmann API for url %s", url)
            raise InvalidAuth("Invalid API key")
        if resp.status == 429:
            # Try to parse retry-after headers if present
            retry_after = None
            if "Retry-After" in resp.headers:
                try:
                    retry_after = int(resp.headers.get("Retry-After"))
                except Exception:
                    retry_after = None
            if "x-ratelimit-retry-after" in resp.headers:
                try:
                    retry_after = int(resp.headers.get("x-ratelimit-retry-after"))
                except Exception:
                    pass
            raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
        _LOGGER.debug("Response status %s for %s", resp.status, url)
        resp.raise_for_status()
        body = await resp.json()
        _LOGGER.debug("Response JSON for %s: %s", url, {k: body.get(k) for k in list(body)[:5]})
        return body

    async def async_get_current(self, latitude: float, longitude: float) -> dict[str, Any]:
        url = f"https://api.kachelmannwetter.com/v02/current/{latitude}/{longitude}"
        return await self._get(url)

    async def async_get_forecast(self, latitude: float, longitude: float) -> dict[str, Any]:
        #url = f"https://api.kachelmannwetter.com/v02/forecast/{latitude}/{longitude}/trend14days"
        url = f"https://api.kachelmannwetter.com/v02/forecast/{latitude}/{longitude}/advanced/6h"
        return await self._get(url)
