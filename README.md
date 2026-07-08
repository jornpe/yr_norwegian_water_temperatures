<img src="https://brands.home-assistant.io/_/yr_norwegian_water_temperatures/icon.png" alt="Description" height="70" align="right" />

# Home assistant YR water temperatures integration


[![GitHub release](https://img.shields.io/github/release/jornpe/Yr-norwegian-water-temperatures-integration?include_prereleases=&sort=semver&color=blue)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/releases/)
[![License](https://img.shields.io/badge/License-MIT-blue)](#license)
[![issues - Yr-norwegian-water-temperatures-integration](https://img.shields.io/github/issues/jornpe/Yr-norwegian-water-temperatures-integration)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/issues)
[![Build, Test, Release](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/actions/workflows/release.yml/badge.svg)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/actions/workflows/release.yml)
[![HACS validation](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/actions/workflows/hacs.yml/badge.svg)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/actions/workflows/hacs.yml)


[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration)  
Must be added as a custom repository.


## Overview

Custom integration for Home Assistant to get Norwegian water temperatures from Yr.no.


This integration provides water temperature data from Norwegian bathing locations via the Yr.no API. It creates an entity for each monitored location showing current water temperature and other relevant information.

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
2. Extract the contents to your `custom_components/yr_norwegian_water_temperatures` directory
3. Restart Home Assistant

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click the **Add Integration** button
3. Search for "YR Norwegian Water Temperatures"
4. Enter your API key from [badetemperaturer.yr.no](https://badetemperaturer.yr.no)
5. Configure the integration options (see below)

### Configuration Options

The integration supports several configuration options that can be set during initial setup or modified later through the integration's options:

#### Required Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| **API Key** | Your API key from [badetemperaturer.yr.no](https://badetemperaturer.yr.no) | *Required* |

#### Optional Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| **Scan Interval** | How often to check for updates (in seconds) | 3600 (1 hour) |
| **Get All Locations** | Monitor all available locations from the API | `false` |
| **Locations** | Comma-separated list of specific location names or IDs to monitor | *Empty* |
| **Automatic Cleanup** | Enable automatic removal of inactive sensors | `true` |
| **Days to Keep Inactive Sensors** | Number of days to keep sensors that haven't been updated | 365 |

#### Location Configuration

You have two options for selecting which locations to monitor:

1. **Monitor All Locations**: Enable "Get all locations" to automatically create sensors for all available locations from the API
2. **Monitor Specific Locations**: Leave "Get all locations" disabled and specify location names or IDs in the "Locations" field

To find specific location names or IDs:
1. Visit [yr.no/nb/badetemperaturer](https://www.yr.no/nb/badetemperaturer)
2. Find your desired location
3. Use either the location name (as displayed) or the ID from the URL
4. Add multiple locations separated by commas

**Example**: `Rognstranda, Barkevik, 1-32236, Kjerkegårdsbukta`

#### Automatic Cleanup

The integration includes an automatic cleanup feature to manage sensors for locations that are no longer receiving updates from the API:

- **Enabled by default**: Sensors that haven't been updated for the specified number of days will be automatically removed
- **Recommended when monitoring all locations**: Prevents accumulation of hundreds of inactive sensors
- **Configurable retention period**: Default is 365 days, minimum is 1 day

⚠️ **Important**: If you disable automatic cleanup while monitoring all locations, you may end up with hundreds of inactive sensors over time.

### Modifying Configuration

To modify the integration configuration after setup:

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Find "YR Norwegian Water Temperatures"
3. Click **Configure** to modify options
4. Click **Reconfigure** to change the API key and other settings

## Features

- **Real-time water temperature data** from Norwegian bathing locations
- **Flexible location monitoring** - monitor all locations or specific ones
- **Automatic sensor management** with configurable cleanup
- **Cached data storage** to prevent sensor loss during API outages
- **Configurable update intervals** (minimum 60 seconds)
- **Case-insensitive location matching** for names and IDs

## Sensors

Each monitored location creates a sensor with:
- **Entity ID**: `sensor.[location_name]`
- **State**: Current water temperature in °C
- **Attributes**: Additional location information from the API

## Troubleshooting

### Common Issues

1. **Invalid API Key**: Ensure your API key from [badetemperaturer.yr.no](https://badetemperaturer.yr.no) is correct
2. **No sensors appearing**: Check if your specified locations exist or try enabling "Get all locations"
3. **Sensors disappearing**: If automatic cleanup is enabled, sensors inactive for the configured period will be removed
4. **High number of sensors**: If monitoring all locations, enable automatic cleanup to prevent sensor accumulation

### Getting Help

- Check the [issues page](https://github.com/jornpe/Yr-norwegian-water-temperatures-integration/issues) for known problems
- Create a new issue if you encounter bugs or need assistance
- Include relevant log entries from Home Assistant when reporting issues

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
