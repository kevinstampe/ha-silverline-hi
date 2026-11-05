# Silverline Hi+ for Home Assistant

[![GitHub release](https://img.shields.io/github/v/release/kevinstampe/ha-silverline-hi)](https://github.com/kevinstampe/ha-silverline-hi/releases)
[![Validate](https://github.com/kevinstampe/ha-silverline-hi/actions/workflows/validate.yaml/badge.svg)](https://github.com/kevinstampe/ha-silverline-hi/actions/workflows/validate.yaml)
[![CI](https://github.com/kevinstampe/ha-silverline-hi/actions/workflows/ci.yaml/badge.svg)](https://github.com/kevinstampe/ha-silverline-hi/actions/workflows/ci.yaml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/github/license/kevinstampe/ha-silverline-hi)](LICENSE)

Control and monitor Silverline Hi+ connected cooker hoods from Home Assistant, using the same cloud service as the Silverline Hi+ app.

> [!NOTE]
> This is an unofficial, community-made integration. It is not affiliated with, endorsed by, or supported by Silverline. It uses an undocumented cloud API that may change without notice.

## Supported devices

Cooker hoods that can be controlled from the **Silverline Hi+** app. Tested with a hood connected through a SilverConnect module. Sensors your hood does not have (for example temperature or CO2) report `0`.

## Installation

### Marketplace / HACS (recommended)

[![Open your Home Assistant instance and open this repository in the Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kevinstampe&repository=ha-silverline-hi&category=integration)

Or add it manually:

1. Open the Marketplace (HACS before Home Assistant 2026.11).
2. Add `https://github.com/kevinstampe/ha-silverline-hi` as a custom repository with the category **Integration**.
3. Install **Silverline Hi+** and restart Home Assistant if asked.

### Manual

1. Download the latest [release](https://github.com/kevinstampe/ha-silverline-hi/releases).
2. Copy `custom_components/silverline_hi` into the `custom_components` folder of your Home Assistant configuration.
3. Restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up Silverline Hi+.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=silverline_hi)

Or go to **Settings → Devices & services → Add integration → Silverline Hi+**.

| Field | Description |
| --- | --- |
| Email | The email you use to log in to the Silverline Hi+ app. |
| Password | The password you use to log in to the Silverline Hi+ app. |

Each hood on the account is added as its own device. If your password changes, Home Assistant asks you to re-authenticate.

## Entities

| Entity | Type | Description |
| --- | --- | --- |
| *(hood name)* | Light | Hood light on/off |
| Fan speed | Number | Fan speed, `0` (off) to the hood's maximum |
| Ventilation timer | Number | Run-on timer in seconds, in 1-minute steps |
| Auto mode | Switch | Let the hood control the fan speed automatically |
| Air quality | Sensor | Air quality in % |
| Humidity | Sensor | Relative humidity |
| Temperature | Sensor | Temperature in °C |
| CO2 | Sensor | CO2 equivalent in ppm |
| VOC | Sensor | Volatile organic compounds in ppm |
| Pressure | Sensor | Air pressure in hPa |
| Carbon filter remaining | Sensor (diagnostic) | Time left before the carbon filter should be replaced |
| Grease filter remaining | Sensor (diagnostic) | Time left before the grease filter should be cleaned |
| SilverConnect status | Sensor (diagnostic) | Raw connection status of the SilverConnect module |
| Hob-to-hood setting | Sensor (diagnostic) | Raw hob-to-hood setting |
| Reset carbon filter | Button (config) | Reset the carbon filter timer after replacing it |
| Reset grease filter | Button (config) | Reset the grease filter timer after cleaning it |

## Example automation

Turn the hood light off when the fan has been off for 10 minutes:

```yaml
automation:
  - alias: Hood light off after cooking
    triggers:
      - trigger: numeric_state
        entity_id: number.kitchen_hood_fan_speed
        below: 1
        for: "00:10:00"
    actions:
      - action: light.turn_off
        target:
          entity_id: light.kitchen_hood
```

## Data updates

The integration polls the Silverline cloud every 30 seconds. Changes made in the app or on the hood itself show up after the next poll.

## Known limitations

- Requires an internet connection; there is no local control.
- Changes can take up to 30 seconds to show up in Home Assistant.
- The light only supports on/off.
- SilverConnect status and hob-to-hood setting are shown as raw values, because their meaning is not documented.

## Troubleshooting

- **Invalid email or password**: check that you can log in to the Silverline Hi+ app with the same credentials.
- **Entities are unavailable**: the Silverline cloud may be down, or the hood may be offline. Check the app.
- **Reporting a problem**: enable debug logging on the integration page, reproduce the problem, then download diagnostics from the integration page and attach both to a [bug report](https://github.com/kevinstampe/ha-silverline-hi/issues/new/choose). Diagnostics remove your email, password and serial number.

## Removal

1. Go to **Settings → Devices & services → Silverline Hi+**, open the ⋮ menu and select **Delete**.
2. Remove the repository from the Marketplace / HACS, or delete `custom_components/silverline_hi` if you installed manually.
3. Restart Home Assistant.

## Development

```sh
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## License

[MIT](LICENSE)
