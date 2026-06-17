"""Integration: DefaultAzureCredential (deploy auth) using tests/.test.env."""

import pytest

from core_api.auth.azure_default_credential import DefaultAzureCredentialAuthenticator
from powerbi_gitlab.constants import FABRIC_API_ROOT


@pytest.mark.integration
def test_default_azure_credential_acquires_fabric_token(
    require_default_azure_credential_env,
) -> None:
    token = DefaultAzureCredentialAuthenticator().acquire_token()
    assert token


@pytest.mark.integration
def test_default_azure_credential_can_read_workspace(
    fabric_api_client,
    fabric_workspace_id: str,
) -> None:
    url = f"{FABRIC_API_ROOT}/workspaces/{fabric_workspace_id}"
    workspace = next(fabric_api_client.call("GET", url))

    assert workspace.get("id") == fabric_workspace_id
