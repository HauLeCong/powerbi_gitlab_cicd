import os

from dotenv import load_dotenv
from msal import ConfidentialClientApplication, TokenCache

from .base import BaseAuthenticator
from .scopes import DEFAULT_FABRIC_SCOPES

load_dotenv()


class FabricServicePrincipalAuthenticator(BaseAuthenticator):

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        scopes: list[str] | None = None,
    ):
        super().__init__()
        self._token_cache = TokenCache()
        self._client_id = client_id or os.getenv("MS_CLIENT_ID")
        self._client_secret = client_secret or os.getenv("MS_CLIENT_SECRET")
        self._scopes = scopes if scopes is not None else DEFAULT_FABRIC_SCOPES.copy()

        if not self._client_id or not self._client_secret:
            raise RuntimeError("Please provide client credentials (MS_CLIENT_ID, MS_CLIENT_SECRET)")

        if not self._scopes:
            raise RuntimeError("At least one Fabric API scope is required")

        tenant_id = os.getenv("MS_TENANT_ID")
        if not tenant_id:
            raise RuntimeError("MS_TENANT_ID is required")

        self._client_app = ConfidentialClientApplication(
            client_id=self._client_id,
            client_credential=self._client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            token_cache=self._token_cache,
        )

    def acquire_token(self) -> str:
        result = self._client_app.acquire_token_for_client(scopes=self._scopes)
        if "access_token" in result:
            return result["access_token"]
        raise RuntimeError(f"Failed to acquire token: {result}")
