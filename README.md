# Resideo Leak Detectors for Home Assistant

[![Build Status][build-status-shield]][build-status]
![Maintenance][maintenance-shield]
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

[![Buy Me A Coffee][buy-me-a-coffee-shield]][buy-me-a-coffee]

A custom [Home Assistant](https://www.home-assistant.io/) integration for
Resideo / Honeywell Home Wi-Fi Water Leak & Freeze Detectors
(`L1_SmartWaterSensor`, also sold under the First Alert brand).

The official `lyric` integration only supports thermostats. This integration
adds the leak detectors that `lyric` leaves out, as a standalone integration
that coexists with `lyric` (different domain, `resideo_leak`).

## Features

Read-only monitoring via the Resideo cloud API, one config entry per account,
across every home (location) on that account.

| Platform | Entity | Source |
| --- | --- | --- |
| `binary_sensor` | Leak (moisture) | `waterPresent` |
| `binary_sensor` | Connectivity | `isDeviceOffline` |
| `binary_sensor` | Problem | `currentAlarms` |
| `sensor` | Temperature | `currentSensorReadings.temperature` |
| `sensor` | Humidity | `currentSensorReadings.humidity` |
| `sensor` | Battery | `batteryRemaining` |
| `sensor` | Wi-Fi signal | `wifiSignalStrength` |
| `sensor` | Last check-in (diagnostic) | `lastCheckin` |

The Problem sensor exposes an `active_alarms` attribute listing the raw alarm
types (e.g. `HighTemperature`, `HighHumidity`), so automations keep working
even for alarm types Resideo has not documented.

## Requirements

- Home Assistant 2026.6 or newer (Python 3.14).
- A Resideo / Honeywell Home account with at least one leak detector.
- Your own Resideo developer app credentials (see Setup). This is the same
  model the official `lyric` integration uses: each user brings their own
  Client ID / Secret. There is no username/password-only path — Resideo only
  offers the OAuth2 authorization-code flow.

## Installation

### HACS (custom repository)

1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/parrot-tailor/ha-resideo-leak-detectors` with
   category **Integration**.
3. Install **Resideo Leak Detectors** and restart Home Assistant.

### Manual

Copy `custom_components/resideo_leak` into your Home Assistant
`config/custom_components/` directory and restart.

## Setup

### 1. Create a Resideo developer app

1. Sign in at the
   [Resideo developer dashboard](https://developer.honeywellhome.com) and
   create an app.
2. Set the app's **Callback URL** to
   `https://my.home-assistant.io/redirect/oauth` (or, if you do not use My
   Home Assistant, `https://<your-ha-url>/auth/external/callback`).
3. Note the **Consumer Key** (Client ID) and **Consumer Secret**
   (Client Secret).

### 2. Add application credentials

In Home Assistant, go to **Settings → Devices & services → Helpers →
Application Credentials** (or you will be prompted during setup) and add the
Consumer Key as the Client ID and the Consumer Secret as the Client Secret.

### 3. Add the integration

Go to **Settings → Devices & services → Add integration → Resideo Leak
Detectors** and complete the OAuth sign-in with your regular Resideo account
(not the developer account).

## Notes and limitations

- **Update cadence.** The detectors report temperature/humidity only 1–3
  times per day (configurable in the Resideo app). Home Assistant polls every
  5 minutes, so leak/alarm state is reasonably fresh but climate readings lag
  between device check-ins.
- **No real-time leak push.** The documented cloud API is polling only; there
  is no push channel, so leak detection is bounded by the poll interval.
- **Read-only.** No settings are written back (buzzer mute, thresholds, etc.).

## Development

```bash
make deps    # create venv (Python 3.14.4) + install dev/test tooling
make check   # ruff + ruff format --check + markdownlint + pyright + pytest
make format  # auto-fix ruff issues
```

The pinned `pytest-homeassistant-custom-component` selects the exact Home
Assistant version tested against (see `requirements-dev.txt`).

## Credits and disclaimer

Architecture mirrors the official Home Assistant `lyric` integration. Brand
images are Resideo's, bundled locally under
`custom_components/resideo_leak/brand/`.

Not affiliated with or endorsed by Resideo Technologies, Inc. or Honeywell.

## License

Released under the [MIT License](LICENSE).

[build-status]: https://github.com/parrot-tailor/ha-resideo-leak-detectors/actions/workflows/ci.yml?query=branch%3Amain
[build-status-shield]: https://img.shields.io/github/actions/workflow/status/parrot-tailor/ha-resideo-leak-detectors/ci.yml?branch=main&style=for-the-badge
[buy-me-a-coffee]: https://buymeacoffee.com/parrot.tailor.coffee
[buy-me-a-coffee-shield]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/parrot-tailor/ha-resideo-leak-detectors.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/maintenance/yes/2026?style=for-the-badge
[releases]: https://github.com/parrot-tailor/ha-resideo-leak-detectors/releases
[releases-shield]: https://img.shields.io/github/v/release/parrot-tailor/ha-resideo-leak-detectors.svg?style=for-the-badge
