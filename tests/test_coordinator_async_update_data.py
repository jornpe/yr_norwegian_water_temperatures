"""Tests for the coordinator module, specifically the _async_update_data function."""
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.yr_norwegian_water_temperatures.coordinator import ApiCoordinator
from custom_components.yr_norwegian_water_temperatures.const import CONF_LOCATIONS, CONF_GET_ALL_LOCATIONS

from tests.conftest import mock_location

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
            return coordinator

    @pytest.mark.asyncio
    async def test_get_all_locations_when_configured(self, coordinator):
        """Test that all locations are returned when get_all_locations is True."""
        # Setup
        mock_locations = [
            mock_location("1", "Oslo"),
            mock_location("2", "Bergen"),
            mock_location("3", "Trondheim")
        ]
        coordinator.client.async_get_all_water_temperatures.return_value = mock_locations
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute
        result = await coordinator._async_update_data()

        # Assert
        assert result == mock_locations
        assert len(result) == 3

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
        coordinator.client.async_get_all_water_temperatures.return_value = mock_locations
        
        # Configure with lowercase location IDs
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: ["loc1", "loc3"]  # lowercase in config
        }

        # Execute
        result = await coordinator._async_update_data()

        # Assert - should match LOC1 and Loc3 despite case differences
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
        mock_locations = [
            mock_location("1", "OSLO"),
            mock_location("2", "bergen"),
            mock_location("3", "Trondheim"),
            mock_location("4", "stavanger")
        ]
        coordinator.client.async_get_all_water_temperatures.return_value = mock_locations
        
        # Configure with lowercase location names
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: ["oslo", "trondheim"]  # lowercase in config
        }

        # Execute
        result = await coordinator._async_update_data()

        # Assert - should match OSLO and Trondheim despite case differences
        assert len(result) == 2
        location_names = [loc.name for loc in result]
        assert "OSLO" in location_names
        assert "Trondheim" in location_names
        assert "bergen" not in location_names
        assert "stavanger" not in location_names

    @pytest.mark.asyncio
    async def test_filter_locations_mixed_id_and_name(self, coordinator):
        """Test filtering with both IDs and names in the configuration."""
        # Setup
        mock_locations = [
            mock_location("BEACH1", "Copacabana"),
            mock_location("2", "OSLO"),
            mock_location("harbor3", "Bergen Port"),
            mock_location("4", "stavanger")
        ]
        coordinator.client.async_get_all_water_temperatures.return_value = mock_locations
        
        # Configure with mix of IDs and names (all lowercase)
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: ["beach1", "oslo", "harbor3"]  # mix of ID and name
        }

        # Execute
        result = await coordinator._async_update_data()

        # Assert
        assert len(result) == 3
        # Should match by ID: BEACH1, harbor3 and by name: OSLO
        result_ids = [loc.location_id for loc in result]
        result_names = [loc.name for loc in result]
        
        assert "BEACH1" in result_ids  # matched by ID
        assert "2" in result_ids       # matched by name (OSLO)
        assert "harbor3" in result_ids # matched by ID
        assert "OSLO" in result_names
        assert "4" not in result_ids   # stavanger not in config

    @pytest.mark.asyncio
    async def test_empty_locations_config_returns_empty_list(self, coordinator):
        """Test that empty locations configuration returns empty list (current behavior - might also be a bug)."""
        # Setup
        mock_locations = [
            mock_location("1", "Oslo"),
            mock_location("2", "Bergen")
        ]
        coordinator.client.async_get_all_water_temperatures.return_value = mock_locations
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False,
            CONF_LOCATIONS: []  # empty list
        }

        # Execute
        result = await coordinator._async_update_data()

        # Assert - Empty list should return empty list (this might be correct behavior)
        assert result == []

    @pytest.mark.asyncio
    async def test_no_locations_config_returns_none(self, coordinator):
        """Test that missing locations configuration returns None (current behavior - this is the bug!)."""
        # Setup
        mock_locations = [
            mock_location("1", "Oslo"),
            mock_location("2", "Bergen")
        ]
        coordinator.client.async_get_all_water_temperatures.return_value = mock_locations
        coordinator.config_entry.options = {
            CONF_GET_ALL_LOCATIONS: False
            # CONF_LOCATIONS not set
        }

        # Execute
        result = await coordinator._async_update_data()

        # Assert - This demonstrates the bug: it returns None instead of empty list or all locations
        assert result == []

    @pytest.mark.asyncio
    async def test_api_error_raises_update_failed(self, coordinator):
        """Test that API errors are properly handled and raise UpdateFailed."""
        # Setup
        coordinator.client.async_get_all_water_temperatures.side_effect = Exception("API Error")
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute & Assert
        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()
        
        assert "Error fetching data: API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_permission_error_raises_update_failed(self, coordinator):
        """Test that permission errors (invalid API key) are properly handled."""
        # Setup
        coordinator.client.async_get_all_water_temperatures.side_effect = PermissionError("Invalid API key")
        coordinator.config_entry.options = {CONF_GET_ALL_LOCATIONS: True}

        # Execute & Assert
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
