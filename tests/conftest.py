import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from core_api.api.fabric import FabricApiClient
from powerbi_gitlab.auth_builders import fabric_client_default_credential

TEST_ENV_PATH = Path(__file__).parent / ".test.env"

AZURE_CREDENTIAL_KEYS = (
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
    "AZURE_TENANT_ID",
)


@pytest.fixture(scope="session", autouse=True)
def load_test_env() -> None:
    if TEST_ENV_PATH.is_file():
        load_dotenv(TEST_ENV_PATH, override=True)


@pytest.fixture
def require_default_azure_credential_env() -> None:
    missing = [
        key for key in AZURE_CREDENTIAL_KEYS if not (os.getenv(key) or "").strip()
    ]
    if missing:
        pytest.skip(
            f"Fill tests/.test.env ({', '.join(AZURE_CREDENTIAL_KEYS)}): "
            f"missing {', '.join(missing)}"
        )


@pytest.fixture
def fabric_api_client(require_default_azure_credential_env) -> FabricApiClient:
    return fabric_client_default_credential()


@pytest.fixture
def fabric_workspace_id() -> str:
    workspace_id = (os.getenv("FABRIC_WORKSPACE_ID") or "").strip()
    if not workspace_id:
        pytest.skip("Set FABRIC_WORKSPACE_ID in tests/.test.env")
    return workspace_id
