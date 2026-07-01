"""Test setup, entity state, and unload of the integration."""

from http import HTTPStatus

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.resideo_leak.const import API_BASE


@pytest.mark.usefixtures("setup_credentials")
async def test_setup_creates_entities(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    locations: list,
) -> None:
    """Setup loads the entry and exposes the expected entity states."""
    aioclient_mock.get(f"{API_BASE}/locations", json=locations)
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED

    assert hass.states.get("binary_sensor.test_laundry_leak").state == "off"
    assert hass.states.get("binary_sensor.test_garage_leak").state == "on"
    assert (
        hass.states.get("binary_sensor.test_garage_connectivity").state
        == "off"
    )
    assert hass.states.get("binary_sensor.test_garage_problem").state == "on"
    assert hass.states.get("sensor.test_laundry_temperature").state == "19.94"
    assert hass.states.get("sensor.test_laundry_humidity").state == "49.9"
    assert hass.states.get("sensor.test_laundry_battery").state == "39"

    problem = hass.states.get("binary_sensor.test_garage_problem")
    assert problem.attributes["active_alarms"] == ["HighHumidity"]


@pytest.mark.usefixtures("setup_credentials")
async def test_unload_entry(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    locations: list,
) -> None:
    """Unloading a loaded entry succeeds and marks it not loaded."""
    aioclient_mock.get(f"{API_BASE}/locations", json=locations)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.usefixtures("setup_credentials")
async def test_setup_auth_error_triggers_reauth(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A 401 on first refresh puts the entry into a setup-error state."""
    aioclient_mock.get(f"{API_BASE}/locations", status=HTTPStatus.UNAUTHORIZED)
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
