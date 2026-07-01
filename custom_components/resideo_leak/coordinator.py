"""Data update coordinator for the Resideo Leak Detectors integration."""

import asyncio
from datetime import timedelta
from http import HTTPStatus
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiohttp import ClientError, ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ResideoApiClient
from .const import DEFAULT_UPDATE_INTERVAL, DEVICE_CLASS_LEAK, DOMAIN
from .models import LeakDevice

_LOGGER = logging.getLogger(__name__)

type ResideoLeakConfigEntry = ConfigEntry[ResideoLeakCoordinator]


def _zone(name: str | None) -> ZoneInfo | None:
    """Resolve an IANA time zone name.

    Args:
        name: IANA time zone name (e.g. ``America/Los_Angeles``), or None.

    Returns:
        The matching ZoneInfo, or None if the name is missing or unknown.
    """
    if not name:
        return None
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return None


class ResideoLeakCoordinator(DataUpdateCoordinator[dict[str, LeakDevice]]):
    """Poll the Resideo cloud for water leak detector state."""

    config_entry: ResideoLeakConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ResideoLeakConfigEntry,
        client: ResideoApiClient,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            config_entry: Config entry owning this coordinator.
            client: Resideo API client used to fetch device state.
        """
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, LeakDevice]:
        """Fetch leak detectors across every location on the account.

        Returns:
            Mapping of device id to its parsed LeakDevice snapshot.

        Raises:
            ConfigEntryAuthFailed: When the token or API rejects the
                credentials (token 400/401/403, or /locations 401/403).
            UpdateFailed: On transient network or server errors.
        """
        # Refresh the OAuth token first. A 400/401/403 from the token endpoint
        # means the refresh token can no longer be used (Honeywell returns 400
        # invalid_grant when it expires), so trigger reauth instead of retrying
        # forever. 429/5xx are transient and stay retryable.
        try:
            await self.client.async_get_access_token()
        except ClientResponseError as err:
            if err.status in (
                HTTPStatus.BAD_REQUEST,
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.FORBIDDEN,
            ):
                raise ConfigEntryAuthFailed from err
            raise UpdateFailed(err) from err
        except (ClientError, TimeoutError) as err:
            raise UpdateFailed(err) from err

        try:
            async with asyncio.timeout(30):
                locations = await self.client.get_locations()
        except ClientResponseError as err:
            if err.status in (
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.FORBIDDEN,
            ):
                raise ConfigEntryAuthFailed from err
            raise UpdateFailed(err) from err
        except (ClientError, TimeoutError) as err:
            raise UpdateFailed(err) from err

        devices: dict[str, LeakDevice] = {}
        # HA TIMESTAMP sensors need tz-aware datetimes; fall back to the HA
        # configured zone if a location omits its IANA time zone.
        default_tz = _zone(self.hass.config.time_zone)
        for location in locations:
            tz = _zone(location.get("ianaTimeZone")) or default_tz
            location_id = location.get("locationID")
            for raw in location.get("devices", []):
                if raw.get("deviceClass") != DEVICE_CLASS_LEAK:
                    continue
                device = LeakDevice.from_api(location_id, raw, tz)
                devices[device.device_id] = device
        return devices
