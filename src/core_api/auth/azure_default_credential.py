from azure.identity import DefaultAzureCredential

from .base import BaseAuthenticator

FABRIC_DEFAULT_SCOPE = "https://api.fabric.microsoft.com/.default"


class DefaultAzureCredentialAuthenticator(BaseAuthenticator):
    """Deploy auth: same credential chain as fabric-cicd (AZURE_* env vars)."""

    def __init__(
        self,
        credential: DefaultAzureCredential | None = None,
        scope: str = FABRIC_DEFAULT_SCOPE,
    ):
        super().__init__()
        self._credential = credential or DefaultAzureCredential()
        self._scope = scope

    def acquire_token(self) -> str:
        return self._credential.get_token(self._scope).token
