import logging
from datetime import timedelta, datetime

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.helpers.storage import Store

from yrwatertemperatures import WaterTemperatures, WaterTemperatureData

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, CONF_LOCATIONS, CONF_GET_ALL_LOCATIONS, STORAGE_KEY, STORAGE_VERSION

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

            # Save the updated data to storage
            _LOGGER.debug(f"Saving {len(self.data)} new locations to storage")
            await self.store.async_save(self.data)

            monitored_locations = self.config_entry.options.get(CONF_LOCATIONS, None)
            get_all_locations = self.config_entry.options.get(CONF_GET_ALL_LOCATIONS, False)

            # Case: if user has specified to get all locations, return all
            if get_all_locations:
                _LOGGER.debug("Returning all locations because of configuration option")
                return self.data

            # Case: if no locations stored or user does not monitor any locations
            # and has not specified to get all, return empty list
            if not self.data or not monitored_locations:
                _LOGGER.warning("No locations found or no monitored locations configured.")
                return []

            # Case: if user has specified monitored locations, filter the data
            # Convert monitored locations to lowercase list for case-insensitive comparison
            monitored_locations_list = [str(loc).strip().lower() for loc in monitored_locations.split(',') if loc.strip()]
            # Filter locations by ID or name, case-insensitive
            locations = [loc for loc in self.data
                    if str(loc.location_id).lower() in monitored_locations_list
                    or loc.name.lower() in monitored_locations_list]

            _LOGGER.debug(f"Returning {len(locations)} monitored locations")
            return locations


        except PermissionError as e:
            _LOGGER.error("Invalid API key")
            raise UpdateFailed(e) from e
        except Exception as e:
            _LOGGER.exception("Error fetching data")
            raise UpdateFailed(f"Error fetching data: {e}") from e