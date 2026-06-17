import json
import os

DEFAULT_FABRIC_SCOPES = ["https://api.fabric.microsoft.com/.default"]


def parse_fabric_scopes(raw: str | None = None) -> list[str]:
    """Parse MS_FABRIC_SCOPE into a list for MSAL acquire_token_for_client."""
    value = raw if raw is not None else os.getenv("MS_FABRIC_SCOPE")
    if not value or not value.strip():
        return DEFAULT_FABRIC_SCOPES.copy()

    value = value.strip()
    if value.startswith("["):
        parsed = json.loads(value)
        if not isinstance(parsed, list) or not all(isinstance(s, str) for s in parsed):
            raise ValueError("MS_FABRIC_SCOPE must be a JSON array of strings")
        return parsed

    if "," in value:
        return [scope.strip() for scope in value.split(",") if scope.strip()]

    return [scope for scope in value.split() if scope]
