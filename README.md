
<img src="https://brands.home-assistant.io/_/yr_norwegian_water_temperatures/icon.png" alt="Description" height="70" align="right" />

# YR Norwegian water temperatures


[![GitHub release](https://img.shields.io/github/release/jornpe/Yr-norwegian-water-temperatures-integration?include_prereleases=&sort=semver&color=blue)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/releases/)
[![License](https://img.shields.io/badge/License-MIT-blue)](#license)
[![issues - Yr-norwegian-water-temperatures-integration](https://img.shields.io/github/issues/jornpe/Yr-norwegian-water-temperatures-integration)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/issues)
[![Build, Test, Release](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/actions/workflows/release.yml/badge.svg)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/actions/workflows/release.yml)
[![HACS validation](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/actions/workflows/hacs.yml/badge.svg)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/actions/workflows/hacs.yml)


[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration)  
Must be added as a custom repository.


Custom integration for Home Assistant to get Norwegian water temperatures from Yr.no.

## Overview

This integration provides water temperature data from Norwegian bathing locations via the Yr.no API. It creates sensors for each monitored location showing current water temperature and other relevant information.

## Prerequisites

- Home Assistant with HACS (Home Assistant Community Store) installed
- API key from [badetemperaturer.yr.no](https://badetemperaturer.yr.no)

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL: `https://github.com/jornpe/Yr-norwegian-water-temperatures-integration`
5. Select category "Integration"
6. Click "Add"
7. Find "YR Norwegian Water Temperatures" in the integrations list and click "Download"
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/releases)
2. Extract the `custom_components/yr-norwegian-water-temperatures` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Getting an API Key

To obtain an API key for this integration:

1. Send an email to **support@yr.no** with the subject line: **"Forespørsel om API-nøkkel til badetemperaturer"**
2. Include in your email:
   - Your name
   - Your email address (contact person)
   - Specify that you want an API key for **retrieving** water temperatures (not sending)
3. Wait for Yr.no support to respond with your API key

**Note**: The API key request process is manual and may take some time to process.

For more detailed information about API keys, visit: [API for mottak av badetemperaturer](https://hjelp.yr.no/hc/no/articles/4402057323154-API-for-mottak-av-badetemperaturer)

### Adding the Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"YR Norwegian Water Temperatures"**
4. Enter your configuration:
   - **API Key**: Your API key from badetemperaturer.yr.no
   - **Scan Interval**: How often to update data in seconds (minimum 60 seconds, default 3600 seconds)
   - **Get All Locations**: Check this to monitor all available locations
   - **Locations**: If not getting all locations, enter specific location names or IDs (comma-separated)

### Configuration Options

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| API Key | Your API key from badetemperaturer.yr.no | - | Yes |
| Scan Interval | Update frequency in seconds (min: 60, recommended: 3600) | 3600 seconds | Yes |
| Get All Locations | Monitor all available water temperature locations | No | No |
| Locations | Specific locations to monitor (comma-separated names or IDs) | - | No* |

*Required if "Get All Locations" is disabled

### Finding Location Names

To find specific location names or IDs:

**Method 1: Using the integration**
1. Enable "Get All Locations" temporarily to see all available sensors
2. Note down the location names or IDs you want to monitor
3. Delete and add the integration again with "Get All Locations" disabled
4. Enter your desired locations in the "Locations" field (e.g., "Oslo, Bergen, 123, Trondheim" - mixing names and IDs)

**Method 2: Using Yr.no website**
1. Visit [https://www.yr.no/nb/badetemperaturer](https://www.yr.no/nb/badetemperaturer)
2. Browse and click on a location you're interested in
3. From the URL, extract the location ID. For example:
   - URL: `https://www.yr.no/nb/værvarsel/daglig-tabell/1-2289869/Norge/Vestfold/Holmestrand/Hagasand`
   - Location ID: `1-2289869`
   - Location name: `Hagasand`
4. Use either the location name (e.g., "Hagasand") or the ID (e.g., "1-2289869") in your configuration

## Usage

Once configured, the integration will create sensors for each monitored location with entities like:
- `sensor.[location_name]`

Each sensor provides:
- Current water temperature
- Location information
- Last updated timestamp
- Source of measurement (only some sensors include this). 

## Troubleshooting

### Common Issues

**"Invalid API key" error**
- Verify your API key is correct
- Ensure your API key is active on badetemperaturer.yr.no

**No sensors appear**
- Check that location names are spelled correctly
- Try enabling "Get All Locations" to see available options
- Verify the integration loaded successfully in the logs

**Data not updating**
- Check your scan interval setting
- Verify network connectivity to Yr.no
- Check Home Assistant logs for error messages

### Support

For issues and feature requests, please visit the [GitHub issues page](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/issues).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


