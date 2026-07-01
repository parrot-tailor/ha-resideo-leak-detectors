"""Resideo API client and OAuth2 implementation bound to Home Assistant."""

from typing import Any, cast

from aiohttp import BasicAuth, ClientSession
from homeassistant.components.application_credentials import AuthImplementation
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE


class ResideoOAuth2Implementation(AuthImplementation):
    """OAuth2 implementation for the Honeywell Home / Resideo cloud.

    Resideo requires the client id/secret in an HTTP Basic auth header on the
    token request (and also accepts them in the body). ``appSelect`` lets the
    user choose between the Resideo and First Alert branded apps at sign-in.
    """

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Return extra query data for the authorize request.

        Returns:
            Parameters that prompt the user to choose the Resideo or First
            Alert app.
        """
        return {"appSelect": "1"}

    async def _token_request(self, data: dict) -> dict:
        """Make a token request with HTTP Basic authentication.

        Args:
            data: Base token request body (grant type, code/refresh token).

        Returns:
            The parsed token response from Resideo.
        """
        session = async_get_clientsession(self.hass)

        data["client_id"] = self.client_id
        if self.client_secret is not None:
            data["client_secret"] = self.client_secret

        headers = {
            "Authorization": BasicAuth(
                self.client_id, self.client_secret
            ).encode(),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with session.post(
            self.token_url, headers=headers, data=data
        ) as resp:
            resp.raise_for_status()
            return cast(dict, await resp.json())


class ResideoApiClient:
    """Minimal async client for the Resideo v2 REST API."""

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
        api_key: str,
    ) -> None:
        """Initialize the client.

        Args:
            websession: Shared aiohttp session from Home Assistant.
            oauth_session: OAuth2 session managing the bearer token.
            api_key: Consumer key (== OAuth client id); the API needs it as
                an ``apikey`` query parameter in addition to the token.
        """
        self._session = websession
        self._oauth = oauth_session
        self._api_key = api_key

    async def async_get_access_token(self) -> str:
        """Return a valid access token, refreshing it if needed.

        Returns:
            The current bearer access token.
        """
        await self._oauth.async_ensure_token_valid()
        return cast(str, self._oauth.token["access_token"])

    async def _get(self, path: str, **params: Any) -> Any:
        """Perform an authenticated GET request.

        Args:
            path: API path appended to the v2 base URL.
            **params: Additional query parameters.

        Returns:
            The parsed JSON response body.
        """
        token = await self.async_get_access_token()
        params["apikey"] = self._api_key
        headers = {"Authorization": f"Bearer {token}"}
        async with self._session.get(
            f"{API_BASE}{path}", params=params, headers=headers
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_locations(self) -> list[dict[str, Any]]:
        """Return all locations with their embedded devices.

        The ``/locations`` payload already embeds full water-leak-detector
        objects, so a single call per poll is enough.

        Returns:
            The list of location objects for the account.
        """
        return cast("list[dict[str, Any]]", await self._get("/locations"))
