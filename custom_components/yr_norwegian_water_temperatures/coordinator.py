import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL

from yrwatertemperatures import WaterTemperatures

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, CONF_LOCATIONS, CONF_GET_ALL_LOCATIONS

_LOGGER = logging.getLogger(__name__)

class ApiCoordinator(DataUpdateCoordinator):
    """Coordinator to fetching data from the API."""

    def __init__(self, hass, config_entry: ConfigEntry):
        """Initialize the coordinator."""

        self.api_key = config_entry.data[CONF_API_KEY]
        self.scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )
        session = async_get_clientsession(hass)
        self.client = WaterTemperatures(self.api_key, session)


    async def _async_update_data(self):
        """Fetch data from the API."""
        try:
            # Fetch water temperatures only for the configured locations, or all if user has specified to get all locations
            locations = await self.client.async_get_all_water_temperatures()
            monitored_locations = self.config_entry.options.get(CONF_LOCATIONS, None)
            if self.config_entry.options.get(CONF_GET_ALL_LOCATIONS, False):
                return locations
            if not locations or not monitored_locations:
                _LOGGER.warning("No locations found or no monitored locations configured.")
                return []

            # Convert monitored locations to lowercase list for case-insensitive comparison
            monitored_locations_list = [str(loc).strip().lower() for loc in monitored_locations.split(',') if loc.strip()]
            # Filter locations by ID or name, case-insensitive
            return [loc for loc in locations
                    if str(loc.location_id).lower() in monitored_locations_list
                    or loc.name.lower() in monitored_locations_list]

        except PermissionError as e:
            _LOGGER.error("Invalid API key")
            raise UpdateFailed(e) from e
        except Exception as e:
            _LOGGER.error(f"Error fetching data: {e}")
            raise UpdateFailed(f"Error fetching data: {e}") from e