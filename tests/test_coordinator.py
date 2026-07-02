"""Test the coordinator's parsing, error mapping, and 401 retry."""

from typing import cast
from unittest.mock import Mock

from aiohttp import ClientResponseError
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.resideo_leak.api import (
    ResideoApiClient,
    ResideoOAuth2Session,
)
from custom_components.resideo_leak.const import DOMAIN
from custom_components.resideo_leak.coordinator import ResideoLeakCoordinator


def _http_error(status: int) -> ClientResponseError:
    """Build a ClientResponseError with the given HTTP status."""
    return ClientResponseError(Mock(), (), status=status)


class _FakeOAuth:
    """Stand-in for ResideoOAuth2Session with scriptable refresh behavior."""

    def __init__(
        self,
        *,
        ensure_error: Exception | None = None,
        force_error: Exception | None = None,
    ) -> None:
        """Store scripted errors and a forced-refresh counter."""
        self._ensure_error = ensure_error
        self._force_error = force_error
        self.forced = 0

    async def async_ensure_token_valid(self) -> None:
        """No-op, or raise the scripted ensure error."""
        if self._ensure_error is not None:
            raise self._ensure_error

    async def force_refresh_token(self) -> None:
        """Count the call, then raise the scripted force error if any."""
        self.forced += 1
        if self._force_error is not None:
            raise self._force_error


class _FakeClient:
    """Stand-in for ResideoApiClient returning scripted get_locations."""

    def __init__(self, results: list) -> None:
        """Store a queue of ('data', payload) / ('error', exc) results."""
        self._results = list(results)
        self.calls = 0

    async def get_locations(self) -> list:
        """Return or raise the next scripted result."""
        self.calls += 1
        kind, value = self._results.pop(0)
        if kind == "error":
            raise value
        return value


def _coordinator(
    hass: HomeAssistant, client: _FakeClient, oauth: _FakeOAuth
) -> ResideoLeakCoordinator:
    """Build a coordinator wired to fake client + oauth session."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    return ResideoLeakCoordinator(
        hass,
        entry,
        cast(ResideoApiClient, client),
        cast(ResideoOAuth2Session, oauth),
    )


async def test_parses_leak_devices(
    hass: HomeAssistant, locations: list
) -> None:
    """Only leak detectors are parsed and keyed by device id."""
    coordinator = _coordinator(
        hass, _FakeClient([("data", locations)]), _FakeOAuth()
    )
    data = await coordinator._async_update_data()
    assert len(data) == 2
    assert "00000000-0000-4000-8000-000000000001" in data


@pytest.mark.parametrize("status", [400, 401, 403])
async def test_token_client_error_triggers_reauth(
    hass: HomeAssistant, status: int
) -> None:
    """A 4xx while refreshing the token raises ConfigEntryAuthFailed."""
    coordinator = _coordinator(
        hass,
        _FakeClient([("data", [])]),
        _FakeOAuth(ensure_error=_http_error(status)),
    )
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_token_server_error_is_retryable(hass: HomeAssistant) -> None:
    """A 5xx while refreshing the token raises UpdateFailed."""
    coordinator = _coordinator(
        hass,
        _FakeClient([("data", [])]),
        _FakeOAuth(ensure_error=_http_error(500)),
    )
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_fetch_401_recovers_after_forced_refresh(
    hass: HomeAssistant, locations: list
) -> None:
    """A single fetch 401 force-refreshes, retries, and succeeds."""
    oauth = _FakeOAuth()
    coordinator = _coordinator(
        hass,
        _FakeClient([("error", _http_error(401)), ("data", locations)]),
        oauth,
    )
    data = await coordinator._async_update_data()
    assert len(data) == 2
    assert oauth.forced == 1


async def test_fetch_401_twice_triggers_reauth(hass: HomeAssistant) -> None:
    """A fetch that 401s even after a forced refresh escalates to reauth."""
    oauth = _FakeOAuth()
    coordinator = _coordinator(
        hass,
        _FakeClient(
            [("error", _http_error(401)), ("error", _http_error(401))]
        ),
        oauth,
    )
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()
    assert oauth.forced == 1


async def test_fetch_401_then_dead_refresh_token(hass: HomeAssistant) -> None:
    """If the forced refresh itself 400s, escalate to reauth."""
    coordinator = _coordinator(
        hass,
        _FakeClient([("error", _http_error(401))]),
        _FakeOAuth(force_error=_http_error(400)),
    )
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_fetch_server_error(hass: HomeAssistant) -> None:
    """A 5xx from /locations raises UpdateFailed (no retry)."""
    coordinator = _coordinator(
        hass,
        _FakeClient([("error", _http_error(503))]),
        _FakeOAuth(),
    )
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
