"""Test the coordinator's parsing and error mapping."""

from typing import cast
from unittest.mock import Mock

from aiohttp import ClientResponseError
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.resideo_leak.api import ResideoApiClient
from custom_components.resideo_leak.const import DOMAIN
from custom_components.resideo_leak.coordinator import ResideoLeakCoordinator


def _http_error(status: int) -> ClientResponseError:
    """Build a ClientResponseError with the given HTTP status."""
    return ClientResponseError(Mock(), (), status=status)


class _FakeClient:
    """Stand-in for ResideoApiClient with scriptable behavior."""

    def __init__(
        self,
        *,
        locations: list | None = None,
        token_error: Exception | None = None,
        locations_error: Exception | None = None,
    ) -> None:
        """Store the scripted responses/errors."""
        self._locations = locations or []
        self._token_error = token_error
        self._locations_error = locations_error

    async def async_get_access_token(self) -> str:
        """Return a token, or raise the scripted token error."""
        if self._token_error is not None:
            raise self._token_error
        return "tok"

    async def get_locations(self) -> list:
        """Return locations, or raise the scripted locations error."""
        if self._locations_error is not None:
            raise self._locations_error
        return self._locations


def _coordinator(
    hass: HomeAssistant, client: _FakeClient
) -> ResideoLeakCoordinator:
    """Build a coordinator wired to a fake client."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    return ResideoLeakCoordinator(hass, entry, cast(ResideoApiClient, client))


async def test_parses_leak_devices(
    hass: HomeAssistant, locations: list
) -> None:
    """Only leak detectors are parsed and keyed by device id."""
    coordinator = _coordinator(hass, _FakeClient(locations=locations))
    data = await coordinator._async_update_data()
    assert len(data) == 2
    assert "00000000-0000-4000-8000-000000000001" in data


@pytest.mark.parametrize("status", [400, 401, 403])
async def test_token_client_error_triggers_reauth(
    hass: HomeAssistant, status: int
) -> None:
    """A 4xx while refreshing the token raises ConfigEntryAuthFailed."""
    coordinator = _coordinator(
        hass, _FakeClient(token_error=_http_error(status))
    )
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_token_server_error_is_retryable(hass: HomeAssistant) -> None:
    """A 5xx while refreshing the token raises UpdateFailed."""
    coordinator = _coordinator(hass, _FakeClient(token_error=_http_error(500)))
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.parametrize("status", [401, 403])
async def test_locations_auth_error(hass: HomeAssistant, status: int) -> None:
    """A 401/403 from /locations raises ConfigEntryAuthFailed."""
    coordinator = _coordinator(
        hass, _FakeClient(locations_error=_http_error(status))
    )
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_locations_server_error(hass: HomeAssistant) -> None:
    """A 5xx from /locations raises UpdateFailed."""
    coordinator = _coordinator(
        hass, _FakeClient(locations_error=_http_error(503))
    )
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
