"""Config flow for the Resideo Leak Detectors integration."""

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN


class ResideoOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle the Resideo OAuth2 config flow."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return the logger for the flow.

        Returns:
            The module logger used by the OAuth2 base flow.
        """
        return logging.getLogger(__name__)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle a reauth triggered by an API authentication error.

        Args:
            entry_data: Data of the config entry needing reauthentication.

        Returns:
            The next config flow step (the reauth confirmation form).
        """
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthentication with the user.

        Args:
            user_input: Submitted form input, or None on first display.

        Returns:
            The confirmation form, or the user step once confirmed.
        """
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    async def async_oauth_create_entry(
        self, data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create the config entry, or update the existing one on reauth.

        Args:
            data: OAuth data (implementation id and token) for the entry.

        Returns:
            A create-entry result, or an abort when an entry already exists.
        """
        existing_entry = await self.async_set_unique_id(DOMAIN)
        if existing_entry:
            self.hass.config_entries.async_update_entry(
                existing_entry, data=data
            )
            await self.hass.config_entries.async_reload(
                existing_entry.entry_id
            )
            return self.async_abort(reason="reauth_successful")
        return self.async_create_entry(
            title="Resideo Leak Detectors", data=data
        )
