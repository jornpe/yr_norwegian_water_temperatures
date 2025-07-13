"""Config flow for the Yr Norwegian Water Temperatures integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL

from yrwatertemperatures import WaterTemperatures

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    CONF_LOCATIONS,
    CONF_GET_ALL_LOCATIONS,
    CONF_ENABLE_CLEANUP,
    CONF_CLEANUP_DAYS,
    DEFAULT_ENABLE_CLEANUP,
    DEFAULT_CLEANUP_DAYS,
    DEFAULT_GET_ALL_LOCATIONS
)

_LOGGER = logging.getLogger(__name__)


def get_options_data_schema(config_entry: ConfigEntry | None) -> vol.Schema:
    """Return the options data schema for the integration."""
    options = config_entry.options if config_entry else {}
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): (vol.All(vol.Coerce(int), vol.Clamp(min=MIN_SCAN_INTERVAL))),
            vol.Optional(
                CONF_GET_ALL_LOCATIONS,
                default=options.get(
                    CONF_GET_ALL_LOCATIONS, DEFAULT_GET_ALL_LOCATIONS
                ),
            ): bool,
            vol.Optional(
                CONF_LOCATIONS, default=options.get(CONF_LOCATIONS, "")
            ): str,
            vol.Optional(
                CONF_ENABLE_CLEANUP,
                default=options.get(CONF_ENABLE_CLEANUP, DEFAULT_ENABLE_CLEANUP),
            ): bool,
            vol.Optional(
                CONF_CLEANUP_DAYS,
                default=options.get(CONF_CLEANUP_DAYS, DEFAULT_CLEANUP_DAYS),
            ): vol.All(vol.Coerce(int), vol.Clamp(min=1)),
        }
    )


def get_user_data_schema(config_entry: ConfigEntry | None) -> vol.Schema:
    """Return the user data schema for the integration."""
    api_key = config_entry.data.get(CONF_API_KEY, "") if config_entry and config_entry.data else ""

    return vol.Schema(
        {
            vol.Required(CONF_API_KEY, default=api_key): str,
        }
    )


def split_user_input(user_input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split user input into data and options dictionaries."""
    data_keys = set()
    for key in get_user_data_schema(None).schema.keys():
        if hasattr(key, 'schema'):
            data_keys.add(key.schema)
        else:
            data_keys.add(str(key))

    options_keys = set()
    for key in get_options_data_schema(None).schema.keys():
        if hasattr(key, 'schema'):
            options_keys.add(key.schema)
        else:
            options_keys.add(str(key))

    data = {key: user_input[key] for key in data_keys if key in user_input}
    options = {key: user_input.get(key) for key in options_keys if key in user_input}

    return data, options


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

                    data, options = split_user_input(user_input)
                    _LOGGER.info(f"Creating {DOMAIN} config entry with data: {data}, options: {options}")

                    return self.async_create_entry(
                        title="YR Water Temperatures",
                        data=data,
                        options= options
                    )

        # Get the options schema dictionary and merge it with the user schema
        options_schema = get_options_data_schema(None).schema
        user_schema = get_user_data_schema(None).schema
        combined_schema = vol.Schema({**user_schema, **options_schema})

        return self.async_show_form(
            step_id="user",
            data_schema=combined_schema,
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

                    data, options = split_user_input(user_input)
                    _LOGGER.info(f"Reconfiguring {DOMAIN} with data: {data}, options: {options}")

                    return self.async_update_reload_and_abort(
                        config_entry,
                        unique_id=config_entry.unique_id,
                        data=data,
                        options = options,
                        reason="reconfigure_successful"
                    )
        # Get the options schema dictionary and merge it with the user schema
        options_schema = get_options_data_schema(config_entry).schema
        user_schema = get_user_data_schema(config_entry).schema
        combined_schema = vol.Schema({**user_schema, **options_schema})

        # Show the reconfiguration form
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=combined_schema,
            errors=errors
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
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Handle the options step."""
        if user_input is not None:
            # Process the user input and update options
            options = self._config_entry.options | user_input
            _LOGGER.info(f"Updating options for {DOMAIN}: {options}")
            return self.async_create_entry(title="", data=options)


        return self.async_show_form(
            step_id="init",
            data_schema=get_options_data_schema(self._config_entry)
        )



class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""