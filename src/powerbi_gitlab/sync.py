"""Git sync workflow: branch → pull → commit. Uses pull.pull_workspace."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core_api.api.fabric import FabricApiClient

from powerbi_gitlab.constants import ITEM_DIR_SUFFIXES
from powerbi_gitlab.pull import pull_workspace


def list_asset_dirs(asset_dir: Path) -> list[Path]:
    if not asset_dir.is_dir():
        return []
    return sorted(
        path
        for path in asset_dir.iterdir()
        if path.is_dir()
        and any(path.name.endswith(suffix) for suffix in ITEM_DIR_SUFFIXES)
    )


def sync_workspace(
    client: FabricApiClient,
    workspace_id: str,
    repo_dir: Path,
    assets_dir: Path,
    branch_name: str,
) -> list[dict[str, Any]]:
    """Create branch, pull workspace into assets_dir, commit if changed."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    _git(repo_dir, "checkout", "-b", branch_name)

    pulled = pull_workspace(client, workspace_id, assets_dir)
    if pulled:
        _commit(repo_dir, workspace_id=workspace_id, item_count=len(pulled))

    return pulled


def _commit(repo_dir: Path, *, workspace_id: str, item_count: int) -> bool:
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        print("No git changes to commit after sync.")
        return False

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    message = (
        f"sync: workspace {workspace_id} ({item_count} items) @ {timestamp}\n\n"
        "Merge this branch into your feature branch, resolve conflicts, then push."
    )
    _git(repo_dir, "commit", "-m", message)
    print(f"Committed sync on branch in {repo_dir.resolve()}")
    return True


def _git(repo_dir: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo_dir, check=True)
