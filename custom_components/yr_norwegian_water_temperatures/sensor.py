"""Sensor definition for the Yr Norwegian Water Temperatures integration."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Mapping, Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from yrwatertemperatures import WaterTemperatureData

from custom_components.yr_norwegian_water_temperatures import (
    RuntimeData,
    YrNorwegianWaterTemperaturesConfigEntry,
)
from custom_components.yr_norwegian_water_temperatures.coordinator import ApiCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: YrNorwegianWaterTemperaturesConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
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

    def __init__(self, coordinator: ApiCoordinator, data: WaterTemperatureData):
        """Initialize the water temperature sensor."""
        super().__init__(coordinator)
        self._data = data
        self._attr_unique_id = data.location_id
        self._attr_native_value = data.temperature

    def _update_from_data(self, data: WaterTemperatureData) -> None:
        """Update the sensor from new coordinator data."""
        self._data = data
        self._attr_native_value = data.temperature

    def _get_coordinator_data(self) -> WaterTemperatureData | None:
        """Return this sensor's data from the coordinator if present."""
        return next(
            (
                data for data in self.coordinator.data or []
                if isinstance(data, WaterTemperatureData) and data.location_id == self._attr_unique_id
            ),
            None
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if data := self._get_coordinator_data():
            self._update_from_data(data)
        self.async_write_ha_state()

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of the sensor."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._data.name

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the latest known temperature."""
        return self._attr_native_value

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
        return {
            "location_id": self._data.location_id,
            "latitude": self._data.latitude,
            "longitude": self._data.longitude,
            "elevation": self._data.elevation,
            "county": self._data.county,
            "municipality": self._data.municipality,
            "source": self._data.source,
            "time": self._data.time.isoformat() if self._data.time else None
        }
