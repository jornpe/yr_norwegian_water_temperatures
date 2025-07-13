"""Sensor definition for the Yr Norwegian Water Temperatures integration."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Mapping, Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.util import dt

from yrwatertemperatures import WaterTemperatureData

from custom_components.yr_norwegian_water_temperatures import RuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform for Yr Norwegian Water Temperatures."""

    coordinator = config_entry.runtime_data.coordinator

    if not coordinator.data:
        _LOGGER.warning("No water temperature data available. Ensure the API is configured correctly.")
        return

    sensors = [
        WaterTemperatureSensor(coordinator, data)
        for data in coordinator.data
        if isinstance(data, WaterTemperatureData)
    ]

    async_add_entities(sensors)

    # Since the API only returns the locations that have been changed recently, we need to
    # look for new sensors that might not be in the initial data and add them dynamically.
    # We will keep track of the known unique IDs to avoid duplicates.
    # Then register a listener to add new sensors when the coordinator updates.
    known_unique_ids = set()
    entity_registry = async_get_entity_registry(hass)

    for entity in entity_registry.entities.values():
        if entity.config_entry_id == config_entry.entry_id:
            known_unique_ids.add(entity.unique_id)


    def _async_add_new_sensors():
        """Add new sensors to HA."""
        new_sensors = [
            WaterTemperatureSensor(coordinator, data)
            for data in coordinator.data
            if isinstance(data, WaterTemperatureData) and data.location_id not in known_unique_ids
        ]

        if new_sensors:
            async_add_entities(new_sensors)
            _LOGGER.debug("Adding new water temperature sensors: %s", [sensor.name for sensor in new_sensors])
            # Update the set of known IDs
            for sensor in new_sensors:
                known_unique_ids.add(sensor.unique_id)

    coordinator_listener = coordinator.async_add_listener(_async_add_new_sensors)

    config_entry.runtime_data = RuntimeData(
        coordinator=coordinator,
        remove_listener=coordinator_listener
    )


class WaterTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a water temperature sensor."""

    def __init__(self, coordinator: DataUpdateCoordinator, data: WaterTemperatureData):
        """Initialize the water temperature sensor."""
        super().__init__(coordinator)
        self.data = data
        self._attr_unique_id = data.location_id
        self._temperature = data.temperature

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of the sensor."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.data.name

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Update the state of the sensor with the latest valid temperature and return it."""
        sensor = next((s for s in self.coordinator.data if s.location_id == self.data.location_id), None)

        self._temperature = sensor.temperature if sensor and sensor.temperature else self._temperature
        return self._temperature

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement for the sensor."""
        return UnitOfTemperature.CELSIUS

    @property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID for the sensor."""
        return self._attr_unique_id

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes of the sensor."""
        new_data = next((s for s in self.coordinator.data if s.location_id == self.data.location_id), None)
        if new_data:
            self.data = new_data
        return {
            "location_id": self.data.location_id,
            "latitude": self.data.latitude,
            "longitude": self.data.longitude,
            "elevation": self.data.elevation,
            "county": self.data.county,
            "municipality": self.data.municipality,
            "source": self.data.source,
            "time": self.data.time.isoformat()
        }