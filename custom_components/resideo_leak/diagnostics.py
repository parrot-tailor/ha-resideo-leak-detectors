"""Diagnostics support for the Resideo Leak Detectors integration."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import ResideoLeakConfigEntry

TO_REDACT = {
    "macID",
    "deviceID",
    "deviceInternalID",
    "userDefinedDeviceName",
    "userDefinedName",
    "name",
    "streetAddress",
    "city",
    "zipcode",
    "username",
    "firstname",
    "lastname",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ResideoLeakConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry holding the coordinator in ``runtime_data``.

    Returns:
        Diagnostics payload with device identifiers and PII redacted.
    """
    coordinator = entry.runtime_data
    return {
        "devices": [
            async_redact_data(device.raw, TO_REDACT)
            for device in coordinator.data.values()
        ]
    }
