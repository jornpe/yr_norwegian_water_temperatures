"""Sensor definition for the Yr Norwegian Water Temperatures integration."""

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from yrwatertemperatures import WaterTemperatureData

from custom_components.yr_norwegian_water_temperatures import (
    RuntimeData,
    YrNorwegianWaterTemperaturesConfigEntry,
)
from custom_components.yr_norwegian_water_temperatures.coordinator import ApiCoordinator

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    class _CoordinatorEntityBase:
        """Type-checking shim for CoordinatorEntity."""

        coordinator: ApiCoordinator

        def __init__(self, coordinator: ApiCoordinator, context: Any = None) -> None:
            """Mirror CoordinatorEntity init for static analysis."""

else:
    _CoordinatorEntityBase = CoordinatorEntity[ApiCoordinator]


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


class WaterTemperatureSensor(_CoordinatorEntityBase, SensorEntity):
    """Representation of a water temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ApiCoordinator, data: WaterTemperatureData):
        """Initialize the water temperature sensor."""
        super().__init__(coordinator)
        self._data = data
        self._attr_unique_id = data.location_id
        self._update_from_data(data)

    def _update_from_data(self, data: WaterTemperatureData) -> None:
        """Update the sensor from new coordinator data."""
        self._data = data
        self._attr_name = data.name
        self._attr_native_value = data.temperature
        self._attr_extra_state_attributes = {
            "location_id": data.location_id,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "elevation": data.elevation,
            "county": data.county,
            "municipality": data.municipality,
            "source": data.source,
            "time": data.time.isoformat() if data.time else None,
        }

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
