"""Application credentials platform for the Resideo Leak Detectors."""

from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .api import ResideoOAuth2Implementation
from .const import OAUTH2_AUTHORIZE, OAUTH2_TOKEN


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return the custom Resideo OAuth2 implementation.

    Args:
        hass: Home Assistant instance.
        auth_domain: Auth domain the credential is registered under.
        credential: Client id/secret entered by the user.

    Returns:
        The Resideo OAuth2 implementation bound to the credential.
    """
    return ResideoOAuth2Implementation(
        hass,
        auth_domain,
        credential,
        AuthorizationServer(
            authorize_url=OAUTH2_AUTHORIZE,
            token_url=OAUTH2_TOKEN,
        ),
    )


async def async_get_description_placeholders(
    hass: HomeAssistant,
) -> dict[str, str]:
    """Return description placeholders for the credentials dialog.

    Args:
        hass: Home Assistant instance.

    Returns:
        Mapping of placeholder names to values shown in the credentials UI.
    """
    return {
        "developer_dashboard_url": "https://developer.honeywellhome.com",
        "redirect_url": "https://my.home-assistant.io/redirect/oauth",
    }
