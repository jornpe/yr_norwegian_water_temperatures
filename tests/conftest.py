"""Test configuration for yr_norwegian_water_temperatures tests."""
from datetime import datetime

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

def load_test_data() -> list[WaterTemperatureData]:
    """Load test data from testdata.json"""
    import json
    from pathlib import Path

    test_data_path = Path(__file__).parent / "testdata.json"
    with open(test_data_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def mock_water_temperature_data() -> list[WaterTemperatureData]:
    """Create a list of mock WaterTemperatureData instances with real Norwegian locations."""
    return [
        WaterTemperatureData(
            location_id="11-17685",
            name="Nordre Jarlsberg Brygge",
            temperature=17.0,
            latitude=59.56648,
            longitude=10.26757,
            elevation=5,
            county="Vestfold",
            municipality="Holmestrand",
            time=datetime.fromisoformat("2025-06-28T09:10:00+02:00"),
            source=""
        ),
        WaterTemperatureData(
            location_id="1-46482",
            name="Løvøya",
            temperature=17,
            latitude=59.4482,
            longitude=10.445,
            elevation=76,
            county="Vestfold",
            municipality="Horten",
            time=datetime.fromisoformat("2025-06-28T15:08:04+02:00"),
            source="Horten kommune"
        ),
        WaterTemperatureData(
            location_id="1-46581",
            name="Nordre Feste",
            temperature=18.0,
            latitude=59.40971,
            longitude=10.65492,
            elevation=15,
            county="Østfold",
            municipality="Moss",
            time=datetime.fromisoformat("2025-06-26T08:30:00+02:00"),
            source=""
        ),
        WaterTemperatureData(
            location_id="1-46628",
            name="Rørestrand",
            temperature=17.5,
            latitude=59.39842,
            longitude=10.47995,
            elevation=2,
            county="Vestfold",
            municipality="Horten",
            time=datetime.fromisoformat("2025-06-28T18:25:41+02:00"),
            source="Horten kommune"
        ),
        WaterTemperatureData(
            location_id="1-46752",
            name="Åsgårdstrand",
            temperature=17.1,
            latitude=59.34938,
            longitude=10.46948,
            elevation=13,
            county="Vestfold",
            municipality="Horten",
            time=datetime.fromisoformat("2025-06-28T15:56:32+02:00"),
            source="Horten kommune"
        ),
        WaterTemperatureData(
            location_id="1-46817",
            name="Eldøya",
            temperature=17.5,
            latitude=59.32306,
            longitude=10.64806,
            elevation=10,
            county="Østfold",
            municipality="Moss",
            time=datetime.fromisoformat("2025-06-28T09:30:00+02:00"),
            source=""
        ),
        WaterTemperatureData(
            location_id="1-46947",
            name="Narverød",
            temperature=16.5,
            latitude=59.25739,
            longitude=10.47646,
            elevation=6,
            county="Vestfold",
            municipality="Tønsberg",
            time=datetime.fromisoformat("2025-06-25T08:50:00+02:00"),
            source=""
        )
    ]
