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

        _LOGGER.info(f"Config for this integration: {config_entry.data}") # TODO: Remove this line

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=self.scan_interval),
        )
        session = async_get_clientsession(hass)
        self.client = WaterTemperatures(self.api_key, session)


    async def _async_update_data(self):
        """Fetch data from the API."""
        _LOGGER.info("Fetching water temperatures from Yr API") # TODO: Remove this line
        try:
            # Fetch water temperatures only for the configured locations, or all if user has specified to get all locations
            locations = await self.client.async_get_all_water_temperatures()
            if self.config_entry.options.get(CONF_GET_ALL_LOCATIONS, False):
                return locations
            monitored_locations = self.config_entry.options.get(CONF_LOCATIONS, None)
            if monitored_locations:
                return [loc for loc in locations
                        if loc.location_id in monitored_locations
                        or loc.name in monitored_locations]

        except PermissionError as e:
            _LOGGER.error("Invalid API key")
            raise UpdateFailed(e) from e
        except Exception as e:
            _LOGGER.error(f"Error fetching data: {e}")
            raise UpdateFailed(f"Error fetching data: {e}") from e