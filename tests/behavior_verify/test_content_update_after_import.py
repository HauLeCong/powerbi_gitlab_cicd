from pathlib import Path
import base64

import pytest
from azure.identity import DefaultAzureCredential
from fabric_cicd import FabricWorkspace, append_feature_flag, publish_all_items, get_changed_items

FIXTURES_DIR = Path(__file__).parent / "fixtures"
RESPONSE_DIR = FIXTURES_DIR / "response_content"

pytestmark = [pytest.mark.behavior_validate, pytest.mark.integration]


def test_report_content_update_after_import(
    fabric_api_client,
    fabric_workspace_id: str,
) -> None:
    if not FIXTURES_DIR.is_dir():
        pytest.skip(f"Missing fixtures directory: {FIXTURES_DIR}")

    # Required to get a return value from publish_all_items (see fabric-cicd docs).
    append_feature_flag("enable_response_collection")

    target_workspace = FabricWorkspace(
        workspace_id=fabric_workspace_id,
        repository_directory=str(FIXTURES_DIR),
        item_type_in_scope=["Report", "SemanticModel"],
        token_credential=DefaultAzureCredential(),
    )

    # Docs: returns Optional[dict] — API responses keyed by item type/name, or None.
    responses = publish_all_items(target_workspace)

    print("publish_all_items() ->", responses)
    
    deployed_reports = target_workspace.deployed_items["Report"]
    # # On each published report
    payload = None
    for report in deployed_reports.keys():
        # if report == "Test report.Report":
        response = fabric_api_client.call("POST", f"https://api.fabric.microsoft.com/v1/workspaces/{fabric_workspace_id}/items/{deployed_reports[report].guid}/getDefinition", json={})
        payload = next(response)
    
    report_payload = None
    for part in payload["definition"]["parts"]:
        if part["path"] == "report.json":
            report_payload = part["payload"]

    with open(FIXTURES_DIR / "Test report.Report" / "report.json", "rb") as f:
        base64_report_string = base64.b64encode(f.read()).decode("utf-8")

    print(base64_report_string)
    assert base64_report_string == report_payload

def test_semantic_model_content_update_after_import(
    fabric_api_client,
    fabric_workspace_id: str,
) -> None:
    if not FIXTURES_DIR.is_dir():
        pytest.skip(f"Missing fixtures directory: {FIXTURES_DIR}")

    # Required to get a return value from publish_all_items (see fabric-cicd docs).
    append_feature_flag("enable_response_collection")

    target_workspace = FabricWorkspace(
        workspace_id=fabric_workspace_id,
        repository_directory=str(FIXTURES_DIR),
        item_type_in_scope=["SemanticModel"],
        token_credential=DefaultAzureCredential(),
    )

    # Docs: returns Optional[dict] — API responses keyed by item type/name, or None.
    responses = publish_all_items(target_workspace)

    print("publish_all_items() ->", responses)
    
    deployed_semantic_models = target_workspace.deployed_items["SemanticModel"]
    # On each published semantic model
    payload = None
    for semantic_model in deployed_semantic_models.keys():
        # if semantic_model == "Test semantic model.SemanticModel":
        response = fabric_api_client.call("POST", f"https://api.fabric.microsoft.com/v1/workspaces/{fabric_workspace_id}/items/{deployed_semantic_models[semantic_model].guid}/getDefinition", json={})
        payload = next(response)

    definition_payload = None
    for part in payload["definition"]["parts"]:
        if part["path"] == "definition.pbism":
            definition_payload = part["payload"]

    with open(FIXTURES_DIR / "Test report.SemanticModel" / "definition.pbism", "rb") as f:
        base64_definition_string = base64.b64encode(f.read()).decode("utf-8")

    assert base64_definition_string == definition_payload

def test_change_detection_function(fabric_api_client, fabric_workspace_id: str) -> None:
    if not FIXTURES_DIR.is_dir():
        pytest.skip(f"Missing fixtures directory: {FIXTURES_DIR}")

    # Required to get a return value from publish_all_items (see fabric-cicd docs).
    append_feature_flag("enable_response_collection")

    target_workspace = FabricWorkspace(
        workspace_id=fabric_workspace_id,
        repository_directory=str(FIXTURES_DIR),
        item_type_in_scope=["Report", "SemanticModel"],
        token_credential=DefaultAzureCredential(),
    )

    changed_items = get_changed_items(target_workspace.repository_directory, git_compare_ref="main")

    assert changed_items == []

    