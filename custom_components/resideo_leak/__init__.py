"""The Resideo Leak Detectors integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
    config_validation as cv,
)

from .api import (
    ResideoApiClient,
    ResideoOAuth2Implementation,
    ResideoOAuth2Session,
)
from .const import DOMAIN
from .coordinator import ResideoLeakConfigEntry, ResideoLeakCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, entry: ResideoLeakConfigEntry
) -> bool:
    """Set up Resideo Leak Detectors from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to set up.

    Returns:
        True when setup succeeds.

    Raises:
        ConfigEntryNotReady: When the OAuth2 implementation is unavailable.
        TypeError: When the resolved implementation is not the Resideo one.
    """
    try:
        implementation = await (
            config_entry_oauth2_flow.async_get_config_entry_implementation(
                hass, entry
            )
        )
    except config_entry_oauth2_flow.ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err

    if not isinstance(implementation, ResideoOAuth2Implementation):
        msg = "Unexpected auth implementation; cannot find OAuth client id"
        raise TypeError(msg)

    session = aiohttp_client.async_get_clientsession(hass)
    oauth_session = ResideoOAuth2Session(hass, entry, implementation)
    client = ResideoApiClient(session, oauth_session, implementation.client_id)

    coordinator = ResideoLeakCoordinator(hass, entry, client, oauth_session)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ResideoLeakConfigEntry
) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to unload.

    Returns:
        True when all platforms unload successfully.
    """
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
