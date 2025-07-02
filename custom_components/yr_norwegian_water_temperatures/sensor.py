"""Sensor definition for the Yr Norwegian Water Temperatures integration."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Mapping, Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from yrwatertemperatures import WaterTemperatureData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform for Yr Norwegian Water Temperatures."""

    coordinator = config_entry.runtime_data.coordinator

    sensors = [
        WaterTemperatureSensor(coordinator, data)
        for data in coordinator.data
        if isinstance(data, WaterTemperatureData)
    ]

    async_add_entities(sensors)


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
    def device_info(self) -> DeviceInfo | None:
        """Return device information for the sensor."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entity_id)},
            name=self.data.name,
            manufacturer="Yr",
            model="Water Temperature Sensor",
            configuration_url="https://www.yr.no/nb/badetemperaturer"
        )

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
        if self.data:
            return {
                "location_id": self.data.location_id,
                "latitude": self.data.latitude,
                "longitude": self.data.longitude,
                "elevation": self.data.elevation,
                "county": self.data.county,
                "municipality": self.data.municipality,
                "source": self.data.source
            }
        return None