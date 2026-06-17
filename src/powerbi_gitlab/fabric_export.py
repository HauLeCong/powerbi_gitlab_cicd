"""Fabric export API — stateless, takes a client. No auth, no git."""

import base64
from pathlib import Path
from typing import Any

from core_api.api.fabric import FabricApiClient

from powerbi_gitlab.constants import FABRIC_API_ROOT, ITEM_TYPES


def list_items(client: FabricApiClient, workspace_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    url = f"{FABRIC_API_ROOT}/workspaces/{workspace_id}/items"
    for page in client.call("GET", url):
        for item in page.get("value", []):
            if item.get("type") in ITEM_TYPES:
                items.append(item)
    return items


def export_item(
    client: FabricApiClient, workspace_id: str, item: dict[str, Any]
) -> dict[str, Any]:
    """Export one item via getDefinition (supports Report/SemanticModel LRO)."""
    url = f"{FABRIC_API_ROOT}/workspaces/{workspace_id}/items/{item['id']}/getDefinition"
    for response in client.call("POST", url, json={}):
        return response
    raise RuntimeError(f"getDefinition returned no response for {item['id']}")


def export_items(
    client: FabricApiClient, workspace_id: str, item_ids: list[str]
) -> dict[str, Any]:
    """Bulk export via bulkExportDefinitions (when supported by the workspace)."""
    url = (
        f"{FABRIC_API_ROOT}/workspaces/{workspace_id}/items/"
        f"bulkExportDefinitions?beta=true"
    )
    body = {"mode": "Selective", "items": [{"id": item_id} for item_id in item_ids]}
    for response in client.call("POST", url, json=body):
        return response
    raise RuntimeError("bulkExportDefinitions returned no response")


def _write_part(target: Path, part: dict[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = part.get("payload", "")
    if part.get("payloadType") == "InlineBase64":
        target.write_bytes(base64.b64decode(payload))
    else:
        target.write_text(payload, encoding="utf-8")


def write_item_definition(
    item: dict[str, Any], definition_response: dict[str, Any], output_dir: Path
) -> list[Path]:
    """Write getDefinition parts under {displayName}.{type}/."""
    item_dir = output_dir / f"{item['displayName']}.{item['type']}"
    written: list[Path] = []
    for part in definition_response.get("definition", {}).get("parts", []):
        target = item_dir / part["path"]
        _write_part(target, part)
        written.append(target)
    return written


def write_files(export_payload: dict[str, Any], output_dir: Path) -> list[Path]:
    """Write bulkExportDefinitions parts (paths include item root folders)."""
    written: list[Path] = []
    for part in export_payload.get("definitionParts", []):
        relative_path = part["path"].lstrip("/")
        target = output_dir / relative_path
        _write_part(target, part)
        written.append(target)
    return written
