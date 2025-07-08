"""Constants for the integration"""
DOMAIN = "yr_norwegian_water_temperatures"

CONF_LOCATIONS = "locations"
CONF_GET_ALL_LOCATIONS = "get_all_locations"

STORAGE_KEY = f"{DOMAIN}_locations_cache" # Key for storing cached locations
STORAGE_VERSION = 1 # Version of the storage format

DEFAULT_SCAN_INTERVAL = 3600  # Default update interval set to every hour
MIN_SCAN_INTERVAL = 60  # Minimum scan interval set to every minute
