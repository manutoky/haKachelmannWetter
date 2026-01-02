"""KachelmannWetter integration for Home Assistant (skeleton)."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # Coordinator created in coordinator.py; import lazily to keep startup fast
    from .coordinator import KachelmannDataUpdateCoordinator

    api_key = entry.data.get("api_key")
    latitude = entry.data.get("latitude")
    longitude = entry.data.get("longitude")

    # Respect configured update interval if provided in options
    from .const import OPTION_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL

    update_interval = entry.options.get(OPTION_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator = KachelmannDataUpdateCoordinator(hass, api_key, latitude, longitude, update_interval_seconds=update_interval)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        # Map invalid auth to AuthFailed so Home Assistant can trigger reauth
        from .exceptions import InvalidAuth

        if isinstance(err, InvalidAuth):
            raise ConfigEntryAuthFailed from err
        raise ConfigEntryNotReady from err

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
