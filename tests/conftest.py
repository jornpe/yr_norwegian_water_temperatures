"""Test configuration for yr_norwegian_water_temperatures tests."""
from datetime import datetime
from typing import Any

import pytest
from unittest.mock import MagicMock, AsyncMock
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY

from yrwatertemperatures import WaterTemperatureData


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {CONF_API_KEY: "test_api_key"}
    entry.options = {}
    return entry


@pytest.fixture
def mock_water_temperatures_client():
    """Create a mock WaterTemperatures client."""
    client = AsyncMock()
    return client


def mock_location(
        location_id: str = "test_location",
        name: str = "Test Name",
        temperature: float = 15.0,
        latitude: float = 60.0,
        longitude: float = 10.0,
        elevation: int = 10,
        county: str = "Test County",
        municipality: str = "Test Municipality",
        time: str = "2023-10-01T12:00:00+00:00",
        source: str = "Test Source") -> WaterTemperatureData:
    """Create a mock WaterTemperatureData instance."""
    return WaterTemperatureData(
        location_id=location_id,
        name=name,
        temperature=temperature,
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        county=county,
        municipality=municipality,
        time=datetime.fromisoformat(time),
        source=source
    )
