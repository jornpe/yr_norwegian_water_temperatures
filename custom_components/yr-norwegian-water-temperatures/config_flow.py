"""Config flow for the Yr Norwegian Water Temperatures integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL

from yrwatertemperatures import WaterTemperatures

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, MIN_SCAN_INTERVAL, CONF_LOCATIONS, CONF_GET_ALL_LOCATIONS
_LOGGER = logging.getLogger(__name__)


def get_user_data_schema(api_key_default="", locations_default="", scan_interval_default=DEFAULT_SCAN_INTERVAL, get_all_locations_default=False) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_API_KEY, default=api_key_default): str,
            vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=scan_interval_default):
                    (vol.All(vol.Coerce(int), vol.Clamp(min=MIN_SCAN_INTERVAL))
            ),
            vol.Optional(CONF_GET_ALL_LOCATIONS, default=get_all_locations_default): bool,
            vol.Optional(CONF_LOCATIONS, default=locations_default): str,
        }
    )

class YrWaterTemperaturesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yr Norwegian Water Temperatures."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Return the options flow handler."""
        return YrWaterTemperaturesOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            if not api_key:
                errors["base"] = "Missing API key"
            else:
                try:
                    await self.validate_api_key(api_key)
                except InvalidAuth:
                    errors[CONF_API_KEY] = "Invalid API key"
                except CannotConnect:
                    errors["base"] = "Unknown"
                else:
                    # If validation succeeds, create the config entry
                    _LOGGER.debug("API key validated successfully")
                    await self.async_set_unique_id(api_key)
                    self._abort_if_unique_id_configured()

                    data = {CONF_API_KEY: user_input[CONF_API_KEY]}
                    options = {
                        CONF_LOCATIONS: user_input.get(CONF_LOCATIONS, ""),
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        CONF_GET_ALL_LOCATIONS: user_input.get(CONF_GET_ALL_LOCATIONS, False)
                    }

                    return self.async_create_entry(
                        title="YR Water Temperatures",
                        data=data,
                        options= options
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=get_user_data_schema(),
            errors=errors
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Handle reconfiguration of the integration."""
        errors = {}
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None:
            _LOGGER.info(f"Reconfiguring {DOMAIN} with user input: {user_input}")
            api_key = user_input.get(CONF_API_KEY)
            if not api_key:
                errors["base"] = "Missing API key"
            else:
                try:
                    await self.validate_api_key(api_key)
                except InvalidAuth:
                    errors[CONF_API_KEY] = "Invalid API key"
                except CannotConnect:
                    errors["base"] = "Unknown"
                else:
                    # If validation succeeds, create the config entry
                    _LOGGER.debug("API key validated successfully")
                    data = {CONF_API_KEY: user_input[CONF_API_KEY]}
                    options = {
                        CONF_LOCATIONS: user_input.get(CONF_LOCATIONS, ""),
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        CONF_GET_ALL_LOCATIONS: user_input.get(CONF_GET_ALL_LOCATIONS, False)
                    }
                    return self.async_update_reload_and_abort(
                        config_entry,
                        unique_id=config_entry.unique_id,
                        data={**config_entry.data, **data},
                        options = {**config_entry.options, **options},
                        reason="reconfigure_successful"
                    )

        # Show the reconfiguration form
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=get_user_data_schema(config_entry.data.get(CONF_API_KEY, ""), config_entry.options.get(CONF_LOCATIONS, ""), config_entry.options.get(CONF_SCAN_INTERVAL))
        )



    async def validate_api_key(self, api_key: str) -> None:
        """Validate api key by making a test API call."""
        try:
            session = async_get_clientsession(self.hass)
            client = WaterTemperatures(api_key, session)
            await client.async_get_all_water_temperatures()
        except PermissionError:
            raise InvalidAuth("Invalid API key")
        except Exception as e:
            _LOGGER.exception("Error connecting to Yr API")
            raise CannotConnect("Cannot connect to Yr API")


class YrWaterTemperaturesOptionsFlow(OptionsFlow):
    """Handle options flow for Yr Norwegian Water Temperatures."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Handle the options step."""
        if user_input is not None:
            # Process the user input and update options
            options = self.options | user_input
            return self.async_create_entry(title="", data=options)

        # Show the options form
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): (vol.All(vol.Coerce(int), vol.Clamp(min=MIN_SCAN_INTERVAL))),
                vol.Optional(CONF_GET_ALL_LOCATIONS, default=self.options.get(CONF_GET_ALL_LOCATIONS, False)): bool,
                vol.Optional(CONF_LOCATIONS, default=self.options.get(CONF_LOCATIONS, "")): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema
        )



class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""