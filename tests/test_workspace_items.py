"""Integration: list workspace Report/SemanticModel items."""

import pytest

from powerbi_gitlab.constants import ITEM_TYPES
from powerbi_gitlab.fabric_export import list_items


@pytest.mark.integration
def test_workspace_has_reports_and_optional_semantic_models(
    fabric_api_client,
    fabric_workspace_id: str,
) -> None:
    items = list_items(fabric_api_client, fabric_workspace_id)

    assert len(items) > 1
    reports = [item for item in items if item.get("type") == "Report"]
    assert reports

    for item in items:
        assert item.get("type") in ITEM_TYPES
        assert item.get("displayName")
