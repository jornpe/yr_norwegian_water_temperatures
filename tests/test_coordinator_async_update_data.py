"""Tests for the coordinator module, specifically the _async_update_data function."""
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.helpers.update_coordinator import UpdateFailed
from custom_components.yr_norwegian_water_temperatures.coordinator import ApiCoordinator
from custom_components.yr_norwegian_water_temperatures.const import CONF_LOCATIONS, CONF_GET_ALL_LOCATIONS
from tests.conftest import mock_location, mock_water_temperature_data, load_test_data
from yrwatertemperatures import WaterTemperatureData

class TestApiCoordinatorAsyncUpdateData:
    """Test the _async_update_data function in ApiCoordinator."""

    @pytest.fixture
    def coordinator(self, mock_hass, mock_config_entry):
        """Create an ApiCoordinator instance for testing."""
        # Ensure mock_config_entry has options attribute
        with patch('custom_components.yr_norwegian_water_temperatures.coordinator.async_get_clientsession'), \
             patch('custom_components.yr_norwegian_water_temperatures.coordinator.WaterTemperatures'):
            coordinator = ApiCoordinator(mock_hass, mock_config_entry)
            coordinator.client = AsyncMock()
            coordinator.config_entry = mock_config_entry
            coordinator.store = AsyncMock()
            return coordinator


    @pytest.mark.asyncio
    async def test_get_all_api_locations_when_configured(self, coordinator):
        """Test that all locations are returned when get_all_locations is True."""
        # Setup
        coordinator.store.async_load.return_value = []
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute
        result = await coordinator._async_update_data()

        # Assert
        assert result == mock_water_temperature_data()
        assert len(result) == len(mock_water_temperature_data())


    @pytest.mark.asyncio
    async def test_get_all_store_locations_when_configured(self, coordinator):
        """Test that all locations are returned when get_all_locations is True."""
        # Setup
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = []
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute
        result = await coordinator._async_update_data()

        # Assert
        assert len(result) == len(load_test_data())


    @pytest.mark.asyncio
    async def test_filter_locations_by_id_case_insensitive(self, coordinator):
        """Test that locations are filtered by ID with case-insensitive matching."""
        # Setup - create locations with mixed case IDs
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

        # Execute
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
        # Setup - create locations with mixed case names
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        
        # Configure with lowercase location names
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: 'løvøya'  # lowercase in config
        }

        # Execute
        result = await coordinator._async_update_data()

        # Assert - should have 1 location matching "Løvøya"
        assert len(result) == 1
        location_names = [loc.name for loc in result]
        assert "Løvøya" in location_names


    @pytest.mark.asyncio
    async def test_filter_locations_by_name_and_id(self, coordinator):
        """Test that locations are filtered by name with case-insensitive matching."""
        # Setup - create locations with mixed case names
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()

        # Configure with lowercase location names
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: 'løvøya, 11-17685, Nordre Feste'
        }

        # Execute
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
        # Setup
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: ''  # empty list
        }

        # Execute
        result = await coordinator._async_update_data()

        # Assert - should return empty list
        assert result == []


    @pytest.mark.asyncio
    async def test_no_locations_config_returns_none(self, coordinator):
        """Test that missing locations configuration returns None (current behavior - this is the bug!)."""
        # Setup
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False
            # CONF_LOCATIONS not set
        }

        # Execute
        result = await coordinator._async_update_data()

        # Assert - should return empty list
        assert result == []


    @pytest.mark.asyncio
    async def test_api_error_raises_update_failed(self, coordinator):
        """Test that API errors are properly handled and raise UpdateFailed."""
        # Setup
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.side_effect = Exception("API Error")
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute & Assert
        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        # Asser - should raise UpdateFailed with the correct message
        assert isinstance(exc_info.value, UpdateFailed)
        assert "Error fetching data: API Error" in str(exc_info.value)


    @pytest.mark.asyncio
    async def test_permission_error_raises_update_failed(self, coordinator):
        """Test that permission errors (invalid API key) are properly handled."""
        # Setup
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.side_effect = PermissionError("Invalid API key")
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute & Assert
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


    @pytest.mark.asyncio
    async def test_loading_data_from_store(self, coordinator):
        """Test that data is loaded from the store and returned correctly."""
        # Setup
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = []
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute
        result = await coordinator._async_update_data()

        # Assert
        assert len(result) == 436

    @pytest.mark.asyncio
    async def test_loading_data_from_store_with_new_location_from_api(self, coordinator):
        """Test that data is loaded from the store and returned correctly."""
        # Setup
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = mock_water_temperature_data()
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute
        result = await coordinator._async_update_data()

        # Assert - should return all locations from store plus new ones from API. The API returns 1 new location.
        assert len(result) == 437

    @pytest.mark.asyncio
    async def test_updateing_store_data_with_api_check_updated_value_is_correct(self, coordinator):
        """Test that data is loaded from the store and returned correctly."""
        # Setup
        coordinator.store.async_load.return_value = load_test_data()
        coordinator.client.async_get_all_water_temperatures.return_value = [
            WaterTemperatureData(
                name="Løvøya",
                location_id="11-17685",
                latitude=59.1234,
                longitude=10.1234,
                elevation=10,
                county="Oslo",
                municipality="Oslo",
                temperature=17.0,  # Updated temperature
                time="2023-10-01T12:00:00+00:00",
                source="Badevann.no"
            )
        ]
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute
        result = await coordinator._async_update_data()

        # Assert - should return updated value for Løvøya
        test_location: WaterTemperatureData = next(loc for loc in result if loc.name == "Løvøya")
        assert test_location.temperature == 17.0