import os

from core_api.api.fabric import FabricApiClient
from core_api.auth.azure_default_credential import (
    DefaultAzureCredentialAuthenticator,
    FABRIC_DEFAULT_SCOPE,
)
from core_api.auth.fabric_service_principal import FabricServicePrincipalAuthenticator
from core_api.auth.scopes import parse_fabric_scopes


def service_principal_authenticator(
    *,
    client_id: str | None = None,
    client_secret: str | None = None,
    tenant_id: str | None = None,
    scopes: list[str] | None = None,
) -> FabricServicePrincipalAuthenticator:
    resolved_client_id = client_id or os.getenv("MS_CLIENT_ID")
    resolved_client_secret = client_secret or os.getenv("MS_CLIENT_SECRET")
    resolved_tenant_id = tenant_id or os.getenv("MS_TENANT_ID")
    resolved_scopes = scopes if scopes is not None else parse_fabric_scopes()

    missing = [
        name
        for name, value in [
            ("MS_CLIENT_ID", resolved_client_id),
            ("MS_CLIENT_SECRET", resolved_client_secret),
            ("MS_TENANT_ID", resolved_tenant_id),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return FabricServicePrincipalAuthenticator(
        client_id=resolved_client_id,
        client_secret=resolved_client_secret,
        scopes=resolved_scopes,
    )


def default_credential_authenticator(
    credential=None,
    scope: str = FABRIC_DEFAULT_SCOPE,
) -> DefaultAzureCredentialAuthenticator:
    return DefaultAzureCredentialAuthenticator(credential=credential, scope=scope)


def fabric_client_service_principal(**kwargs) -> FabricApiClient:
    return FabricApiClient(service_principal_authenticator(**kwargs))


def fabric_client_default_credential(**kwargs) -> FabricApiClient:
    return FabricApiClient(default_credential_authenticator(**kwargs))
