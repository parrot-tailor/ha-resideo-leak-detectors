"""Test the OAuth2 session's proactive-refresh valid_token logic."""

import time

from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.resideo_leak.api import (
    ResideoOAuth2Implementation,
    ResideoOAuth2Session,
)
from custom_components.resideo_leak.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)


def _session(hass: HomeAssistant, token: dict) -> ResideoOAuth2Session:
    """Build a ResideoOAuth2Session holding the given token."""
    impl = ResideoOAuth2Implementation(
        hass,
        DOMAIN,
        ClientCredential("id", "secret"),
        AuthorizationServer(OAUTH2_AUTHORIZE, OAUTH2_TOKEN),
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={"auth_implementation": DOMAIN, "token": token},
    )
    entry.add_to_hass(hass)
    return ResideoOAuth2Session(hass, entry, impl)


def _token(remaining: float, expires_in: object = 1800) -> dict:
    """Build a token dict expiring ``remaining`` seconds from now."""
    return {
        "access_token": "a",
        "refresh_token": "r",
        "token_type": "Bearer",
        "expires_in": expires_in,
        "expires_at": time.time() + remaining,
    }


async def test_fresh_token_is_valid(hass: HomeAssistant) -> None:
    """A token within the first third of life is valid."""
    assert _session(hass, _token(1799)).valid_token is True


async def test_token_past_one_third_is_invalid(hass: HomeAssistant) -> None:
    """A 1800s token with <1200s left is invalid (proactive refresh)."""
    assert _session(hass, _token(1000)).valid_token is False


async def test_string_expires_in_is_coerced(hass: HomeAssistant) -> None:
    """expires_in returned as a string (Honeywell) is handled."""
    assert _session(hass, _token(1000, "1800")).valid_token is False
    assert _session(hass, _token(1799, "1800")).valid_token is True


async def test_missing_expires_in_uses_skew_only(hass: HomeAssistant) -> None:
    """Without expires_in, only the clock-skew margin applies."""
    assert _session(hass, _token(100, 0)).valid_token is True
    assert _session(hass, _token(5, 0)).valid_token is False
