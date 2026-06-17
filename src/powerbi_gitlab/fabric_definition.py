"""Fabric item definitions — read local parts, push (updateDefinition), base64 compare."""

import base64
import json
from pathlib import Path
from typing import Any

from core_api.api.fabric import FabricApiClient

from powerbi_gitlab.constants import FABRIC_API_ROOT
from powerbi_gitlab.fabric_export import export_item


def read_local_parts(item_dir: Path) -> list[dict[str, Any]]:
    """Build updateDefinition parts from a local {name}.{Type}/ folder."""
    parts: list[dict[str, Any]] = []
    for file_path in sorted(item_dir.rglob("*")):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(item_dir).as_posix()
        parts.append(
            {
                "path": relative,
                "payload": base64.b64encode(file_path.read_bytes()).decode("ascii"),
                "payloadType": "InlineBase64",
            }
        )
    return parts


def push_item_definition(
    client: FabricApiClient,
    workspace_id: str,
    item_id: str,
    parts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Push definition parts via updateDefinition (LRO)."""
    url = (
        f"{FABRIC_API_ROOT}/workspaces/{workspace_id}/items/{item_id}/updateDefinition"
    )
    body = {"definition": {"parts": parts}}
    for response in client.call("POST", url, json=body):
        return response
    raise RuntimeError(f"updateDefinition returned no response for {item_id}")


def pull_item_definition(
    client: FabricApiClient, workspace_id: str, item: dict[str, Any]
) -> dict[str, Any]:
    return export_item(client, workspace_id, item)


def parts_base64_map(definition_response: dict[str, Any]) -> dict[str, str]:
    """Map part path → base64 payload string."""
    result: dict[str, str] = {}
    for part in definition_response.get("definition", {}).get("parts", []):
        path = part["path"]
        payload = part.get("payload", "")
        if part.get("payloadType") == "InlineBase64":
            result[path] = payload
        else:
            result[path] = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    return result


def local_parts_base64_map(item_dir: Path) -> dict[str, str]:
    return {part["path"]: part["payload"] for part in read_local_parts(item_dir)}


def item_display_name(item_dir: Path) -> str:
    platform_path = item_dir / ".platform"
    data = json.loads(platform_path.read_text(encoding="utf-8"))
    return data["metadata"]["displayName"]


def item_type_suffix(item_dir: Path) -> str:
    name = item_dir.name
    if name.endswith(".SemanticModel"):
        return "SemanticModel"
    if name.endswith(".Report"):
        return "Report"
    raise ValueError(f"Not a Report/SemanticModel folder: {item_dir}")
