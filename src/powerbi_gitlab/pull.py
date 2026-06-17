"""Pull workspace content to disk. Requires a FabricApiClient (caller provides auth)."""

from pathlib import Path
from typing import Any

from core_api.api.fabric import FabricApiClient

from powerbi_gitlab.constants import ASSETS_DIR
from powerbi_gitlab.fabric_export import export_item, list_items, write_item_definition


def pull_workspace(
    client: FabricApiClient,
    workspace_id: str,
    output_dir: Path = ASSETS_DIR,
) -> list[dict[str, Any]]:
    """Export every Report/SemanticModel in the workspace to output_dir."""
    items = list_items(client, workspace_id)
    if not items:
        print(f"No Report or SemanticModel items in workspace {workspace_id}.")
        return []

    pulled: list[dict[str, Any]] = []
    for item in items:
        payload = export_item(client, workspace_id, item)
        files = write_item_definition(item, payload, output_dir)
        print(f"Pulled {item['displayName']} ({item['type']}): {len(files)} file(s)")
        pulled.append(item)
    return pulled
