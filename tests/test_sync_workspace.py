"""Step 2: sync_workspace — git branch + pull + commit (enable when ready)."""

import subprocess
from datetime import datetime, timezone

import pytest

from powerbi_gitlab.constants import ASSETS_DIR
from powerbi_gitlab.sync import list_asset_dirs, sync_workspace

pytestmark = pytest.mark.skip(reason="Git sync tests — run after pull_workspace tests pass")


def _init_git_repo(repo_dir) -> None:
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "sync-test@local"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "sync-test"], cwd=repo_dir, check=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=repo_dir, check=True)


@pytest.mark.integration
def test_sync_workspace_creates_branch_and_pulls_assets(
    fabric_api_client,
    fabric_workspace_id: str,
    tmp_path,
) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    assets_dir = repo_dir / ASSETS_DIR
    branch_name = f"sync/test-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    _init_git_repo(repo_dir)

    pulled = sync_workspace(
        fabric_api_client,
        fabric_workspace_id,
        repo_dir,
        assets_dir,
        branch_name,
    )

    assert len(pulled) > 1
    assert any(path.name.endswith(".Report") for path in list_asset_dirs(assets_dir))
