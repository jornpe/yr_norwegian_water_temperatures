import logging
from datetime import timedelta, datetime
from typing import Any

from aiohttp import ClientResponseError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.exceptions import ConfigEntryAuthFailed
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


def _water_temperature_from_stored(item: WaterTemperatureData | dict[str, Any]) -> WaterTemperatureData:
    """Convert stored location data to WaterTemperatureData."""
    if isinstance(item, WaterTemperatureData):
        return item

    data = dict(item)
    if isinstance(data.get("time"), str):
        data["time"] = datetime.fromisoformat(data["time"])

    return WaterTemperatureData(**data)


def _water_temperature_to_stored(data: WaterTemperatureData) -> dict[str, Any]:
    """Convert WaterTemperatureData to JSON-safe stored data."""
    return {
        "name": data.name,
        "location_id": data.location_id,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "elevation": data.elevation,
        "county": data.county,
        "municipality": data.municipality,
        "temperature": data.temperature,
        "time": data.time.isoformat() if isinstance(data.time, datetime) else data.time,
        "source": data.source,
    }


def _merge_locations(*location_groups: list[WaterTemperatureData]) -> list[WaterTemperatureData]:
    """Merge locations by ID with later groups taking precedence."""
    merged_locations: dict[str, WaterTemperatureData] = {}

    for locations in location_groups:
        for location in locations:
            merged_locations[location.location_id] = location

    return list(merged_locations.values())


def _serialize_locations(locations: list[WaterTemperatureData]) -> list[dict[str, Any]]:
    """Convert locations to storage format."""
    return [_water_temperature_to_stored(location) for location in locations]


class ApiCoordinator(DataUpdateCoordinator[list[WaterTemperatureData]]):
    """Coordinator to fetching data from the API."""

    def __init__(self, hass, config_entry: ConfigEntry):
        """Initialize the coordinator."""

        self.api_key = config_entry.data[CONF_API_KEY]
        self.scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self._config_entry = config_entry
        self.data: list[WaterTemperatureData]

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )
        session = async_get_clientsession(hass)
        self.client = WaterTemperatures(self.api_key, session)
        self.store = Store[list[dict[str, Any]]](
            hass,
            STORAGE_VERSION,
            STORAGE_KEY)

    async def _async_load_stored_locations(self) -> list[WaterTemperatureData]:
        """Load cached locations from storage."""
        try:
            stored_data = await self.store.async_load()
        except Exception as err:
            _LOGGER.warning("Failed to load cached water temperatures: %s", err)
            return []

        if not stored_data:
            return []

        try:
            stored_locations = [_water_temperature_from_stored(item) for item in stored_data]
        except Exception as err:
            _LOGGER.warning("Failed to deserialize cached water temperatures: %s", err)
            return []

        _LOGGER.debug("Loaded %s locations from storage", len(stored_locations))
        return stored_locations

    async def _async_filter_locations(
        self, locations: list[WaterTemperatureData]
    ) -> list[WaterTemperatureData]:
        """Filter locations based on current config options."""
        get_all_locations = self._config_entry.options.get(CONF_GET_ALL_LOCATIONS, False)
        monitored_locations_config = self._config_entry.options.get(CONF_LOCATIONS, None)

        if not monitored_locations_config and not get_all_locations:
            _LOGGER.warning("No monitored locations configured and not set to get all locations.")
            return []

        if get_all_locations:
            return locations

        monitored_locations_list = [
            str(loc).strip().lower()
            for loc in monitored_locations_config.split(',')
            if loc.strip()
        ]
        monitored_data = [
            loc for loc in locations
            if str(loc.location_id).lower() in monitored_locations_list
            or loc.name.lower() in monitored_locations_list
        ]

        unmonitored_ids = [loc.location_id for loc in locations if loc not in monitored_data]
        if unmonitored_ids:
            await self.cleanup_old_entities(unmonitored_ids)

        return monitored_data

    async def _async_cleanup_stale_locations(
        self, locations: list[WaterTemperatureData]
    ) -> list[WaterTemperatureData]:
        """Remove locations that are too old when cleanup is enabled."""
        if not self._config_entry.options.get(CONF_ENABLE_CLEANUP, False):
            return locations

        cleanup_days = self._config_entry.options.get(CONF_CLEANUP_DAYS, 365)
        cutoff_date = dt.now().astimezone() - timedelta(days=cleanup_days)
        to_remove = [loc for loc in locations if loc.time is not None and loc.time < cutoff_date]
        if not to_remove:
            return locations

        await self.cleanup_old_entities([loc.location_id for loc in to_remove])
        return [loc for loc in locations if loc not in to_remove]

    def _iter_exception_chain(self, err: Exception):
        """Yield an exception and its causes for classification."""
        current: BaseException | None = err
        while current is not None:
            yield current
            current = current.__cause__ or current.__context__

    def _is_auth_failure(self, err: Exception) -> bool:
        """Return True if the failure indicates invalid credentials."""
        for current in self._iter_exception_chain(err):
            if isinstance(current, PermissionError):
                return True
            if isinstance(current, ClientResponseError) and current.status in {401, 403}:
                return True
        return False

    async def cleanup_old_entities(self, location_ids: list[str]) -> None:
        """Remove entities that are no longer in the monitored locations."""
        entity_registry = er.async_get(self.hass)

        # Get all entity IDs for the domain
        entities = er.async_entries_for_config_entry(entity_registry, self._config_entry.entry_id)

        for entity in entities:
            if entity.unique_id in location_ids:
                entity_registry.async_remove(entity.entity_id)
                _LOGGER.debug(f"Removed entity: {entity.entity_id}")


    async def _async_update_data(self) -> list[WaterTemperatureData]:
        """Fetch data from the API."""
        stored_locations = await self._async_load_stored_locations()
        current_locations = getattr(self, "data", []) or []
        fallback_locations = current_locations or stored_locations
        try:
            # Fetch water temperatures and merge existing data not in the API response
            updated_locations = await self.client.async_get_all_water_temperatures()
            merged_locations = _merge_locations(stored_locations, current_locations, updated_locations)
            filtered_locations = await self._async_filter_locations(merged_locations)
            filtered_locations = await self._async_cleanup_stale_locations(filtered_locations)

            self.data = filtered_locations
            await self.store.async_save(_serialize_locations(merged_locations))

            return self.data

        except PermissionError as err:
            raise ConfigEntryAuthFailed("Invalid API key") from err
        except Exception as err:
            if self._is_auth_failure(err):
                raise ConfigEntryAuthFailed("Invalid API key") from err

            if fallback_locations:
                filtered_fallback = await self._async_filter_locations(fallback_locations)
                self.data = filtered_fallback
                _LOGGER.warning(
                    "Yr API update failed; using %s cached water temperature readings: %s",
                    len(filtered_fallback),
                    err,
                )
                return self.data

            _LOGGER.exception("Error fetching data and no cached data is available")
            raise UpdateFailed(f"Error fetching data: {err}") from err