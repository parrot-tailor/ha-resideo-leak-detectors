"""Test the Resideo Leak Detectors OAuth2 config flow."""

from http import HTTPStatus
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_setup_component
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.resideo_leak.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
REDIRECT = "https://example.com/auth/external/callback"
SETUP = "custom_components.resideo_leak.async_setup_entry"


@pytest.fixture
async def mock_impl(hass: HomeAssistant) -> None:
    """Register application credentials for the flow."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET), "cred"
    )


async def test_abort_without_credentials(hass: HomeAssistant) -> None:
    """The flow aborts when no application credentials are configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "missing_credentials"


@pytest.mark.usefixtures("current_request_with_host", "mock_impl")
async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A user completes OAuth and a config entry is created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {"flow_id": result["flow_id"], "redirect_uri": REDIRECT},
    )

    assert result["type"] is FlowResultType.EXTERNAL_STEP
    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT}"
        f"&state={state}&appSelect=1"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == HTTPStatus.OK

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(SETUP, return_value=True) as mock_setup:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"]
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["auth_implementation"] == "cred"
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.unique_id == DOMAIN
    assert entry.state is ConfigEntryState.LOADED
    assert len(mock_setup.mock_calls) == 1


@pytest.mark.usefixtures("current_request_with_host", "mock_impl")
async def test_reauth_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Reauth updates the existing entry and aborts as successful."""
    old_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={"auth_implementation": "cred"},
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {"flow_id": result["flow_id"], "redirect_uri": REDIRECT},
    )
    client = await hass_client_no_auth()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(SETUP, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"]
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
