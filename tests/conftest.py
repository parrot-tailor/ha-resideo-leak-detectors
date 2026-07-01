"""Shared fixtures for the Resideo Leak Detectors tests."""

import json
from pathlib import Path
import time

from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.resideo_leak.const import DOMAIN

CLIENT_ID = "test-client-id"
CLIENT_SECRET = "test-client-secret"

FIXTURE = Path(__file__).parent / "fixtures" / "leak_locations.json"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading the custom integration in every test."""
    return


@pytest.fixture
def locations() -> list:
    """Return the sanitized /locations API payload."""
    return json.loads(FIXTURE.read_text())


@pytest.fixture
async def setup_credentials(hass: HomeAssistant) -> None:
    """Register application credentials for the integration."""
    assert await async_setup_component(hass, "application_credentials", {})
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET)
    )


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry holding a still-valid token."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        title="Resideo Leak Detectors",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": time.time() + 3600,
                "expires_in": 3600,
                "token_type": "Bearer",
            },
        },
    )
