"""Yr norwegian water temperature integration"""

from __future__ import annotations

from __future__ import annotations
import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .coordinator import ApiCoordinator

_LOGGER = logging.getLogger(__name__)

# List fo platforms this integration will support
PLATFORMS = [Platform.SENSOR]

@dataclass
class RuntimeData:
    """Class to hold runtimedata"""
    coordinator: DataUpdateCoordinator
    remove_listener: Callable[[], None] | None = None


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up config entry"""

    coordinator = ApiCoordinator(hass, config_entry)

    # Perform initial data loaf from api
    # This raises ConfigEntryNotReady if it fails
    await coordinator.async_config_entry_first_refresh()

    # Add coordinator to runtime data to make it available
    # for the rest of the integration
    config_entry.runtime_data = RuntimeData(coordinator)

    # Register the update listener to handle updates to the config entry
    config_entry.async_on_unload(config_entry.add_update_listener(async_update_listener))

    # Setup platforms (based on the list of entity types in PLATFORMS defined above)
    # This calls the async_setup method in each of the entity type files.
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entries"""
    # Remove the coordinator listener
    if entry.runtime_data and entry.runtime_data.remove_listener:
        entry.runtime_data.remove_listener()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok

async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle updates to the config entry."""
    _LOGGER.debug("Config entry updated: %s", entry.data)
    await hass.config_entries.async_reload(entry.entry_id)