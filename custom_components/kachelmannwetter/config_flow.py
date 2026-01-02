"""Config flow for KachelmannWetter integration."""
from __future__ import annotations

from logging import Logger, getLogger

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from .client import KachelmannClient

_LOGGER: Logger = getLogger(__package__)


class KachelmannConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        _LOGGER.debug("async_step_user called; user_input present=%s", user_input is not None)
        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            lat = user_input[CONF_LATITUDE]
            lon = user_input[CONF_LONGITUDE]
            client = KachelmannClient(self.hass, api_key)
            _LOGGER.debug("Testing KachelmannClient with provided credentials")
            try:
                await client.async_get_current(lat, lon)
            except Exception as err:
                # Map known exceptions to form errors
                from .exceptions import InvalidAuth

                if isinstance(err, InvalidAuth):
                    errors["base"] = "auth"
                else:
                    errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="KachelmannWetter", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_LATITUDE): float,
                vol.Required(CONF_LONGITUDE): float,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, user_input=None):
        """Handle re-authentication."""
        errors = {}
        _LOGGER.debug("async_step_reauth called; user_input present=%s", user_input is not None)
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            entry = self.context.get("entry")
            client = KachelmannClient(self.hass, api_key)
            try:
                await client.async_get_current(entry.data.get(CONF_LATITUDE), entry.data.get(CONF_LONGITUDE))
            except Exception as err:
                from .exceptions import InvalidAuth

                if isinstance(err, InvalidAuth):
                    errors["base"] = "auth"
                else:
                    errors["base"] = "cannot_connect"
            else:
                # update the entry with the new key
                entry.data[CONF_API_KEY] = api_key
                self.hass.config_entries.async_update_entry(entry, data=entry.data)
                return self.async_abort(reason="reauth_successful")

        schema = vol.Schema({vol.Required(CONF_API_KEY): str})
        return self.async_show_form(step_id="reauth", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return KachelmannOptionsFlow(entry)


class KachelmannOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input=None):
        from .const import OPTION_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, MIN_UPDATE_INTERVAL, MAX_UPDATE_INTERVAL

        if user_input is not None:
            return self.async_create_entry(title="options", data=user_input)

        schema = vol.Schema({vol.Optional(OPTION_UPDATE_INTERVAL, default=self.entry.options.get(OPTION_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)): int})
        return self.async_show_form(step_id="init", data_schema=schema)
