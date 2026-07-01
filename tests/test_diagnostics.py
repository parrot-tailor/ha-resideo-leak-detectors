"""Test config entry diagnostics redaction."""

from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.resideo_leak.const import API_BASE
from custom_components.resideo_leak.diagnostics import (
    async_get_config_entry_diagnostics,
)


@pytest.mark.usefixtures("setup_credentials")
async def test_diagnostics_redacts_pii(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    locations: list,
) -> None:
    """Diagnostics redact identifiers/PII but keep sensor readings."""
    aioclient_mock.get(f"{API_BASE}/locations", json=locations)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    devices = result["devices"]
    assert len(devices) == 2
    first = devices[0]
    assert first["macID"] == REDACTED
    assert first["deviceID"] == REDACTED
    assert first["userDefinedDeviceName"] == REDACTED
    assert "temperature" in first["currentSensorReadings"]
    assert first["waterPresent"] in (True, False)
