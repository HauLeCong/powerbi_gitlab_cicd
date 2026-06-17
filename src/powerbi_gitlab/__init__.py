"""powerbi_gitlab — GitLab ↔ Fabric for Report and SemanticModel.

Layout:
  constants.py    shared paths and item types
  fabric_export.py  Fabric API: list_items, export_items, write_files
  pull.py           pull_workspace(client, workspace_id, output_dir)
  sync.py           sync_workspace(client, ..., branch_name)
  deploy.py         deploy_workspace(config, environment)
  auth_builders.py  optional auth helpers for scripts/tests
"""
