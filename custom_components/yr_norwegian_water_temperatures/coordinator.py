import logging
from datetime import timedelta, datetime

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.helpers.storage import Store
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt

from yrwatertemperatures import WaterTemperatures, WaterTemperatureData

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    CONF_LOCATIONS,
    CONF_GET_ALL_LOCATIONS,
    STORAGE_KEY,
    STORAGE_VERSION,
    CONF_ENABLE_CLEANUP,
    CONF_CLEANUP_DAYS,
)

_LOGGER = logging.getLogger(__name__)

class ApiCoordinator(DataUpdateCoordinator):
    """Coordinator to fetching data from the API."""

    def __init__(self, hass, config_entry: ConfigEntry):
        """Initialize the coordinator."""

        self.api_key = config_entry.data[CONF_API_KEY]
        self.scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self.data: list[WaterTemperatureData]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )
        session = async_get_clientsession(hass)
        self.client = WaterTemperatures(self.api_key, session)
        self.store = Store[list[WaterTemperatureData]](
            hass,
            STORAGE_VERSION,
            STORAGE_KEY)

    async def cleanup_old_entities(self, location_ids: list[str]) -> None:
        """Remove entities that are no longer in the monitored locations."""
        entity_registry = er.async_get(self.hass)

        # Get all entity IDs for the domain
        entities = er.async_entries_for_config_entry(entity_registry, self.config_entry.entry_id)

        for entity in entities:
            if entity.unique_id in location_ids:
                entity_registry.async_remove(entity.entity_id)
                _LOGGER.debug(f"Removed entity: {entity.entity_id}")


    async def _async_update_data(self):
        """Fetch data from the API."""

        try:
            # Load cached data if available
            if stored_data := await self.store.async_load():
                self.data = [
                    WaterTemperatureData(**{**item, 'time': datetime.fromisoformat(item['time'])})
                    for item in stored_data
                ]
                _LOGGER.debug(f"Loaded {len(self.data)} locations from storage")

            # Fetch water temperatures and merge existing data not in the API response
            updated_locations = await self.client.async_get_all_water_temperatures()
            updated_ids = set(loc.location_id for loc in updated_locations)

            if self.data:
                for existing_location in self.data:
                    if existing_location.location_id not in updated_ids:
                        updated_locations.append(existing_location)

            self.data = updated_locations

            get_all_locations = self.config_entry.options.get(CONF_GET_ALL_LOCATIONS, False)
            monitored_locations_config = self.config_entry.options.get(CONF_LOCATIONS, None)

            # User has not specified to get all locations and no monitored locations configured, returning an empty list and logging a warning
            if not monitored_locations_config and not get_all_locations:
                _LOGGER.warning("No monitored locations configured and not set to get all locations.")
                return []

            # Filter self.data to only include monitored locations if not getting all locations
            if not get_all_locations:
                if monitored_locations_config:
                    monitored_locations_list = [str(loc).strip().lower() for loc in
                                                monitored_locations_config.split(',') if loc.strip()]
                    monitored_data = [loc for loc in self.data
                                      if str(loc.location_id).lower() in monitored_locations_list
                                      or loc.name.lower() in monitored_locations_list]

                    # Remove unmonitored entities
                    unmonitored_ids = [loc.location_id for loc in self.data if loc not in monitored_data]
                    if unmonitored_ids:
                        await self.cleanup_old_entities(unmonitored_ids)

                    self.data = monitored_data

            # Clean up old entities if automatic cleanup is enabled
            if self.config_entry.options.get(CONF_ENABLE_CLEANUP, False):
                cleanup_days = self.config_entry.options.get(CONF_CLEANUP_DAYS, 365)
                cutoff_date = dt.now().astimezone() - timedelta(days=cleanup_days)
                to_remove = [loc for loc in self.data if loc.time < cutoff_date]
                if to_remove:
                    await self.cleanup_old_entities([loc.location_id for loc in to_remove])
                    self.data = [loc for loc in self.data if loc not in to_remove]

            return self.data


        except PermissionError as e:
            _LOGGER.error("Invalid API key")
            raise UpdateFailed(e) from e
        except Exception as e:
            _LOGGER.exception("Error fetching data")
            raise UpdateFailed(f"Error fetching data: {e}") from e