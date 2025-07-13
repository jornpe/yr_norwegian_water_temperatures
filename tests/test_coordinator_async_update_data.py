"""Tests for the coordinator module, specifically the _async_update_data function."""
from datetime import datetime, timedelta

import pytest
from unittest.mock import AsyncMock, patch, Mock
from homeassistant.helpers.update_coordinator import UpdateFailed
from custom_components.yr_norwegian_water_temperatures.coordinator import ApiCoordinator
from custom_components.yr_norwegian_water_temperatures.const import *
from tests.conftest import mock_location, mock_water_temperature_data, load_test_data
from yrwatertemperatures import WaterTemperatureData

class TestApiCoordinatorAsyncUpdateData:
    """Test the _async_update_data function in ApiCoordinator."""

    @pytest.fixture
    def coordinator(self, mock_hass, mock_config_entry, monkeypatch):
        """Create an ApiCoordinator instance for testing."""
        # Ensure mock_config_entry has options attribute
        monkeypatch.setattr('custom_components.yr_norwegian_water_temperatures.coordinator.async_get_clientsession', AsyncMock())
        monkeypatch.setattr('custom_components.yr_norwegian_water_temperatures.coordinator.er', AsyncMock())

        coordinator = ApiCoordinator(mock_hass, mock_config_entry)
        coordinator.client = AsyncMock()
        coordinator.config_entry = mock_config_entry
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.store = AsyncMock()

        # Mock the cleanup method
        monkeypatch.setattr(coordinator, 'cleanup_old_entities', AsyncMock())

        return coordinator


    @pytest.mark.asyncio
    async def test_get_all_api_locations_when_configured(self, coordinator):
        """Test that all locations are returned when get_all_locations is True."""
        # Arrange
        coordinator.store.async_load.return_value = []
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Act
        result = await coordinator._async_update_data()

        # Assert
        assert result == mock_water_temperature_data()
        assert len(result) == len(mock_water_temperature_data())


    @pytest.mark.asyncio
    async def test_get_all_store_locations_when_configured(self, coordinator):
        """Test that all locations are returned when get_all_locations is True."""
        # Arrange
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = []
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Act
        result = await coordinator._async_update_data()

        # Assert
        assert len(result) == len(load_test_data())


    @pytest.mark.asyncio
    async def test_filter_locations_by_id_case_insensitive(self, coordinator):
        """Test that locations are filtered by ID with case-insensitive matching."""
        # Arrange - create locations with mixed case IDs
        mock_locations = [
            mock_location("LOC1", "Oslo"),
            mock_location("loc2", "Bergen"),
            mock_location("Loc3", "Trondheim"),
            mock_location("4", "Stavanger")
        ]
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_locations
        
        # Configure with lowercase location IDs
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: "loc1, loc3"  # lowercase in config
        }

        # Act
        result = await coordinator._async_update_data()

        # Assert - should have 2 locations matching "loc1" and "loc3"
        assert len(result) == 2
        location_ids = [loc.location_id for loc in result]
        assert "LOC1" in location_ids
        assert "Loc3" in location_ids
        assert "loc2" not in location_ids
        assert "4" not in location_ids


    @pytest.mark.asyncio
    async def test_filter_locations_by_name_case_insensitive(self, coordinator):
        """Test that locations are filtered by name with case-insensitive matching."""
        # Arrange - create locations with mixed case names
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        
        # Configure with lowercase location names
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: 'løvøya'  # lowercase in config
        }

        # Act
        result = await coordinator._async_update_data()

        # Assert - should have 1 location matching "Løvøya"
        assert len(result) == 1
        location_names = [loc.name for loc in result]
        assert "Løvøya" in location_names


    @pytest.mark.asyncio
    async def test_filter_locations_by_name_and_id(self, coordinator):
        """Test that locations are filtered by name with case-insensitive matching."""
        # Arrange - create locations with mixed case names
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()

        # Configure with lowercase location names
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: 'løvøya, 11-17685, Nordre Feste'
        }

        # Act
        result = await coordinator._async_update_data()

        # Assert - should have 3 locations matching "Løvøya", "Nordre Jarlsberg Brygge" and "Nordre Feste"
        assert len(result) == 3
        location_names = [loc.name for loc in result]
        assert "Løvøya" in location_names
        assert "Nordre Jarlsberg Brygge" in location_names
        assert "Nordre Feste" in location_names


    @pytest.mark.asyncio
    async def test_empty_locations_config_returns_empty_list(self, coordinator):
        """Test that empty locations configuration returns empty list (current behavior - might also be a bug)."""
        # Arrange
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: ''  # empty list
        }

        # Act
        result = await coordinator._async_update_data()

        # Assert - should return empty list
        assert result == []


    @pytest.mark.asyncio
    async def test_no_locations_config_returns_none(self, coordinator):
        """Test that missing locations configuration returns None (current behavior - this is the bug!)."""
        # Arrange
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False
            # CONF_LOCATIONS not set
        }

        # Act
        result = await coordinator._async_update_data()

        # Assert - should return empty list
        assert result == []


    @pytest.mark.asyncio
    async def test_api_error_raises_update_failed(self, coordinator):
        """Test that API errors are properly handled and raise UpdateFailed."""
        # Arrange
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.side_effect = Exception("API Error")
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Act & Assert
        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        # Should raise UpdateFailed with the correct message
        assert isinstance(exc_info.value, UpdateFailed)
        assert "Error fetching data: API Error" in str(exc_info.value)


    @pytest.mark.asyncio
    async def test_permission_error_raises_update_failed(self, coordinator):
        """Test that permission errors (invalid API key) are properly handled."""
        # Arrange
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.side_effect = PermissionError("Invalid API key")
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Act & Assert
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


    @pytest.mark.asyncio
    async def test_loading_data_from_store(self, coordinator):
        """Test that data is loaded from the store and returned correctly."""
        # Arrange
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = []
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Act
        result = await coordinator._async_update_data()

        # Assert
        assert len(result) == 436

    @pytest.mark.asyncio
    async def test_loading_data_from_store_with_new_location_from_api(self, coordinator):
        """Test that data is loaded from the store and returned correctly."""
        # Arrange
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Act
        result = await coordinator._async_update_data()

        # Assert - should return all locations from store plus new ones from API. The API returns 1 new location.
        assert len(result) == 437


    @pytest.mark.asyncio
    async def test_cleanup_of_old_sensors(self, coordinator, monkeypatch):
        """Test that old sensors are cleaned up when cleanup is enabled."""
        # Arrange
        old_date = datetime.now() - timedelta(days=2)  # Make it 2 days old to ensure cleanup
        mock_now = datetime.now()

        # Mock home assistant datetime module
        mock_dt = Mock()
        mock_dt.now.return_value.astimezone.return_value = mock_now
        monkeypatch.setattr('custom_components.yr_norwegian_water_temperatures.coordinator.dt', mock_dt)


        # Mock dt.now().astimezone() to return a fixed datetime
        mock_now = datetime.now()
        mock_dt.now.return_value.astimezone.return_value = mock_now

        coordinator.store.async_load.return_value = []
        coordinator.client.async_get_all_water_temperatures.return_value = [
            WaterTemperatureData(
                name="Løvøya",
                location_id="11-17685",
                latitude=59.1234,
                longitude=10.1234,
                elevation=10,
                county="Oslo",
                municipality="Oslo",
                temperature=17.0,
                time=old_date,  # Use datetime object that is 2 days old
                source="Badevann.no"
            ),
            WaterTemperatureData(
                name="Nordre Jarlsberg Brygge",
                location_id="11-17686",
                latitude=59.1235,
                longitude=10.1235,
                elevation=10,
                county="Oslo",
                municipality="Oslo",
                temperature=18.0,
                time=datetime.now(),  # Current time for this location
                source="Badevann.no"
            )
        ]
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: True,
            CONF_ENABLE_CLEANUP: True,
            CONF_CLEANUP_DAYS: 1  # Clean up locations older than 1 day
        }

        # Act
        result = await coordinator._async_update_data()

        # Assert - should return no locations as the old one is cleaned up
        assert len(result) == 1

        # Verify that cleanup_old_entities was called with the correct location ID
        coordinator.cleanup_old_entities.assert_called_once_with(['11-17685'])


    @pytest.mark.asyncio
    async def test_cleanup_sensors_not_monitored_anymore(self, coordinator):
        """Test that data is loaded from the store and returned correctly."""
        # Arrange
        coordinator.store.async_load.return_value = []
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: "11-17685, 1-46482",  # Only monitor these two locations
            CONF_ENABLE_CLEANUP: True
        }

        # Act
        result = await coordinator._async_update_data()

        # Assert - should return all locations from store plus new ones from API. The API returns 1 new location.
        assert len(result) == 2
        # Verify that cleanup_old_entities was called with the correct location ID
        coordinator.cleanup_old_entities.assert_called_once_with(
            [loc.location_id for loc in mock_water_temperature_data() if loc.location_id not in ["11-17685", "1-46482"]]
        )