#!/usr/bin/env python3
"""Pull workspace → asset/, or sync_workspace with --git-branch."""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from core_api.api.fabric import FabricApiClient

from powerbi_gitlab.auth_builders import (
    default_credential_authenticator,
    service_principal_authenticator,
)
from powerbi_gitlab.constants import ASSETS_DIR
from powerbi_gitlab.pull import pull_workspace
from powerbi_gitlab.sync import sync_workspace

AUTH_CHOICES = ("service-principal", "default-credential")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-id",
        default=os.environ.get("FABRIC_WORKSPACE_ID"),
        help="Fabric workspace ID (or FABRIC_WORKSPACE_ID)",
    )
    parser.add_argument(
        "--output",
        default=ASSETS_DIR,
        type=Path,
        help=f"Output directory (default: {ASSETS_DIR})",
    )
    parser.add_argument(
        "--auth",
        choices=AUTH_CHOICES,
        default=os.environ.get("FABRIC_AUTH", "service-principal"),
        help="Auth method (default: service-principal or FABRIC_AUTH)",
    )
    parser.add_argument(
        "--git-branch",
        nargs="?",
        const=f"sync/workspace-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        default=None,
        help="Create git branch and commit after pull",
    )
    args = parser.parse_args()

    if not args.workspace_id:
        print("Error: --workspace-id or FABRIC_WORKSPACE_ID is required", file=sys.stderr)
        return 1

    try:
        if args.auth == "service-principal":
            auth = service_principal_authenticator()
        else:
            auth = default_credential_authenticator()
        client = FabricApiClient(auth)

        if args.git_branch:
            sync_workspace(
                client,
                args.workspace_id,
                Path.cwd(),
                args.output,
                args.git_branch,
            )
        else:
            pull_workspace(client, args.workspace_id, args.output)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
