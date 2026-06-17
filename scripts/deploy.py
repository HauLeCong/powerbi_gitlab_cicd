#!/usr/bin/env python3
"""Deploy asset/ to Fabric via fabric-cicd config.yml."""

import argparse
import os
import sys
from pathlib import Path

from powerbi_gitlab.deploy import DEFAULT_GIT_COMPARE_REF, deploy_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=os.environ.get("FABRIC_CONFIG", "config.yml"),
        type=Path,
    )
    parser.add_argument(
        "--environment",
        default=os.environ.get("FABRIC_ENVIRONMENT", "PROD"),
        help="Key in config.yml / parameter.yml (DEV, PPE, PROD)",
    )
    parser.add_argument(
        "--git-compare-ref",
        default=os.environ.get("FABRIC_GIT_COMPARE_REF", DEFAULT_GIT_COMPARE_REF),
        help="Git ref for change detection (or FABRIC_GIT_COMPARE_REF)",
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if not args.config.is_file():
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        return 1

    try:
        deploy_workspace(
            args.config,
            args.environment,
            debug=args.debug,
            git_compare_ref=args.git_compare_ref,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
