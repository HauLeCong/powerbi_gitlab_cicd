"""Step 1: pull_workspace — list + export items from Fabric to disk (no git)."""

import pytest

from powerbi_gitlab.constants import ITEM_TYPES
from powerbi_gitlab.pull import pull_workspace
from powerbi_gitlab.sync import list_asset_dirs


@pytest.mark.integration
def test_pull_workspace_exports_items_to_disk(
    fabric_api_client,
    fabric_workspace_id: str,
    tmp_path,
) -> None:
    output_dir = tmp_path / "asset"

    pulled = pull_workspace(fabric_api_client, fabric_workspace_id, output_dir)

    assert len(pulled) > 1, "Workspace should have more than one Report/SemanticModel"

    reports = [item for item in pulled if item["type"] == "Report"]
    assert reports, "Workspace must include at least one Report"

    for item in pulled:
        assert item["type"] in ITEM_TYPES
        assert item["displayName"]
        assert item["id"]

    item_dirs = list_asset_dirs(output_dir)
    assert len(item_dirs) == len(pulled)
    assert any(path.name.endswith(".Report") for path in item_dirs)

    # Each item folder should contain at least one file
    for path in item_dirs:
        files = [f for f in path.rglob("*") if f.is_file()]
        assert files, f"{path.name} has no exported files"
