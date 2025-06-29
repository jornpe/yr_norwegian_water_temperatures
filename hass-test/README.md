# Home Assistant Test Environment

This Docker Compose setup allows you to test your `yr-norwegian-water-temperatures` custom integration locally without pushing to GitHub.

## Setup

1. Make sure Docker and Docker Compose are installed on your system
2. Navigate to the `hass-test` directory
3. Start Home Assistant:
   ```bash
   docker-compose up -d

## Usage

- Home Assistant will be available at http://localhost:8123
- Your custom integration is automatically mounted from `../custom_components/yr-norwegian-water-temperatures/`
- Configuration is persisted in the `./config` directory

## Development Workflow

1. Make changes to your custom integration in `../custom_components/yr-norwegian-water-temperatures/`
2. Restart Home Assistant to reload the integration:
   ```bash
   docker-compose restart
   ```
3. Test your changes in the Home Assistant UI

## Configuration

To enable your custom integration, add this to `config/configuration.yaml`:

```yaml
yr_norwegian_water_temperatures:
  # Your configuration here
```

## Logs

To view Home Assistant logs:
```bash
docker-compose logs -f homeassistant
```

## Stopping

To stop the test environment:
```bash
docker-compose down
```
