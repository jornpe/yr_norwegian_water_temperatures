"""Tests for the Yr Norwegian Water Temperatures sensor platform."""

from unittest.mock import MagicMock

from custom_components.yr_norwegian_water_temperatures.sensor import WaterTemperatureSensor
from tests.conftest import mock_location
from yrwatertemperatures import WaterTemperatureData


def test_sensor_keeps_last_known_data_when_coordinator_omits_location():
    """Test that a sparse coordinator update does not clear sensor data."""
    coordinator = MagicMock()
    initial_location = mock_location(
        location_id="cached-location",
        name="Cached Beach",
        temperature=15.5,
        time="2025-06-27T09:00:00+02:00",
    )
    omitted_update_location = mock_location(
        location_id="other-location",
        name="Other Beach",
        temperature=17.0,
        time="2025-06-28T09:00:00+02:00",
    )
    coordinator.data = [initial_location]
    sensor = WaterTemperatureSensor(coordinator, initial_location)
    sensor.async_write_ha_state = MagicMock()

    coordinator.data = [omitted_update_location]
    sensor._handle_coordinator_update()

    assert sensor.native_value == 15.5
    assert sensor.extra_state_attributes["time"] == initial_location.time.isoformat()
    sensor.async_write_ha_state.assert_called_once()


def test_sensor_updates_last_known_data_when_coordinator_includes_location():
    """Test that matching coordinator data updates sensor value and attributes."""
    coordinator = MagicMock()
    initial_location = mock_location(
        location_id="cached-location",
        name="Cached Beach",
        temperature=15.5,
        time="2025-06-27T09:00:00+02:00",
    )
    updated_location = mock_location(
        location_id="cached-location",
        name="Cached Beach",
        temperature=18.0,
        time="2025-06-28T09:00:00+02:00",
    )
    coordinator.data = [initial_location]
    sensor = WaterTemperatureSensor(coordinator, initial_location)
    sensor.async_write_ha_state = MagicMock()

    coordinator.data = [updated_location]
    sensor._handle_coordinator_update()

    assert sensor.native_value == 18.0
    assert sensor.extra_state_attributes["time"] == updated_location.time.isoformat()
    sensor.async_write_ha_state.assert_called_once()


def test_sensor_accepts_nullable_water_temperature_fields():
    """Test that nullable API fields are exposed without crashing."""
    coordinator = MagicMock()
    initial_location = mock_location(
        location_id="nullable-location",
        name="Nullable Beach",
        temperature=15.5,
        time="2025-06-27T09:00:00+02:00",
    )
    nullable_location = WaterTemperatureData(
        name="Nullable Beach",
        location_id="nullable-location",
        latitude=None,
        longitude=None,
        elevation=None,
        county=None,
        municipality=None,
        temperature=None,
        time=None,
        source="Manual"
    )
    coordinator.data = [initial_location]
    sensor = WaterTemperatureSensor(coordinator, initial_location)
    sensor.async_write_ha_state = MagicMock()

    coordinator.data = [nullable_location]
    sensor._handle_coordinator_update()

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {
        "location_id": "nullable-location",
        "latitude": None,
        "longitude": None,
        "elevation": None,
        "county": None,
        "municipality": None,
        "source": "Manual",
        "time": None
    }
    sensor.async_write_ha_state.assert_called_once()