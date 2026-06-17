"""Deploy Git content to Fabric via fabric-cicd."""

import os
from pathlib import Path
from typing import Any

import yaml
from azure.identity import DefaultAzureCredential
from fabric_cicd import deploy_with_config, get_changed_items

DEFAULT_GIT_COMPARE_REF = "main"


def repository_directory(config_path: Path) -> Path:
    """Read ``core.repository_directory`` from config.yml (relative to config file)."""
    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)
    rel = config["core"]["repository_directory"]
    path = Path(rel)
    if path.is_absolute():
        return path.resolve()
    return (config_path.resolve().parent / path).resolve()


def deploy_workspace(
    config_path: Path,
    environment: str,
    *,
    debug: bool = False,
    git_compare_ref: str | None = None,
) -> None:
    if debug:
        from fabric_cicd import change_log_level

        change_log_level()

    resolved = config_path.resolve()
    compare_ref = git_compare_ref or os.environ.get(
        "FABRIC_GIT_COMPARE_REF",
        DEFAULT_GIT_COMPARE_REF,
    )
    repo_dir = repository_directory(resolved)

    print(f"Deploying environment '{environment}' using {resolved}...")
    print(f"Repository directory: {repo_dir}")
    print(f"Git compare ref: {compare_ref}")

    changed_items = get_changed_items(repo_dir, git_compare_ref=compare_ref)

    config_override: dict[str, Any] | None = None
    if changed_items:
        print(f"Changed items: {changed_items}")
        config_override = {"publish": {"items_to_include": changed_items}}

    result = deploy_with_config(
        config_file_path=str(resolved),
        token_credential=DefaultAzureCredential(),
        environment=environment,
        config_override=config_override,
    )
    print(result.message)
