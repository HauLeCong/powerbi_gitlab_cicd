# powerbi-gitlab

Deploy and pull **Power BI Reports** and **Semantic Models** between **GitLab** and **Microsoft Fabric**.

See [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for architecture and design decisions.

## Quick start

```bash
poetry install
```

## Authentication

Two paths — deploy and pull use different auth:

| Script | Auth | Before running |
|--------|------|----------------|
| `scripts/deploy.py` | `DefaultAzureCredential` (fabric-cicd) | CI: `AZURE_*` vars — local: `az login` |
| `scripts/pull.py` | Your choice: `--auth service-principal` or `--auth default-credential` | Pass `authenticator`/`client` in code |

### Deploy (local)

```bash
az login
python scripts/deploy.py
```

### Pull

Choose auth with `--auth` (or `FABRIC_AUTH`):

```bash
# service principal (default)
python scripts/pull.py --auth service-principal --workspace-id "$FABRIC_WORKSPACE_ID"

# DefaultAzureCredential (AZURE_* — same as deploy)
python scripts/pull.py --auth default-credential --workspace-id "$FABRIC_WORKSPACE_ID"
```

Service principal env vars:

```env
MS_CLIENT_ID=...
MS_CLIENT_SECRET=...
MS_TENANT_ID=...
MS_FABRIC_SCOPE=["https://api.fabric.microsoft.com/.default"]
```

`MS_FABRIC_SCOPE` is a **scope array**. Supported formats:

- JSON: `["https://api.fabric.microsoft.com/.default"]`
- Comma-separated: `https://api.fabric.microsoft.com/.default,other/.default`
- Space-separated: `https://api.fabric.microsoft.com/.default`

If omitted, defaults to `["https://api.fabric.microsoft.com/.default"]`.

## Deploy configuration (`config.yml`)

Deploy uses [fabric-cicd Configuration Deployment](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/config_deployment/) via `config.yml` — not hard-coded constants.

Workspace IDs from GitLab CI/CD variables via `$ENV:` ([Parameterization — Environment Variable Replacement](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/parameterization/)):

```yaml
features:
  - enable_environment_variable_replacement

core:
  workspace_id:
    DEV: "$ENV:FABRIC_WORKSPACE_ID_DEV"
    PPE: "$ENV:FABRIC_WORKSPACE_ID_PPE"
    PROD: "$ENV:FABRIC_WORKSPACE_ID_PROD"
```

Content folder layout (same as before):

```
./
├── Sales.Report/
├── Sales.SemanticModel/
├── parameter.yml      # see fabric-cicd parameterization docs
└── config.yml         # deploy targets and behaviour
```

## Scripts

### Deploy (Git → workspace)

```bash
python scripts/deploy.py --environment PROD
```

| Flag | Env fallback | Description |
|------|--------------|-------------|
| `--config` | `FABRIC_CONFIG` | Path to `config.yml` (default `config.yml`) |
| `--environment` | `FABRIC_ENVIRONMENT` | Key in `config.yml` + `parameter.yml` (`DEV`, `PPE`, `PROD`) |
| `--debug` | — | fabric-cicd debug logs |

**CI behaviour:** deploys whatever is in Git. No check that `pull` was run first — **Git overwrites** the workspace.

### Pull (workspace → Git)

Export workspace content before commit/push when you edited reports in Fabric.

```bash
python scripts/pull.py --workspace-id "$FABRIC_WORKSPACE_ID" --output .

# Optional: commit on sync branch, then merge into feature branch
python scripts/pull.py --workspace-id "$FABRIC_WORKSPACE_ID" --git-branch
git checkout feature/my-branch
git merge sync/workspace-20250608-120000
```

## GitLab CI

Set variables:

| Variable | Purpose |
|----------|---------|
| `AZURE_CLIENT_ID` | Service principal client ID (deploy auth) |
| `AZURE_CLIENT_SECRET` | Service principal secret (masked) |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `FABRIC_CONFIG` | Path to `config.yml` (default `config.yml`) |
| `FABRIC_ENVIRONMENT` | `DEV`, `PPE`, or `PROD` |
| `FABRIC_WORKSPACE_ID_DEV` | Dev workspace GUID |
| `FABRIC_WORKSPACE_ID_PPE` | PPE workspace GUID |
| `FABRIC_WORKSPACE_ID_PROD` | Prod workspace GUID |
| `FABRIC_CONNECTION_ID_DEV` | Dev semantic model connection GUID |
| `FABRIC_CONNECTION_ID_PPE` | PPE semantic model connection GUID |
| `FABRIC_CONNECTION_ID_PROD` | Prod semantic model connection GUID |

Pipeline (`.gitlab-ci.yml`):

```yaml
script:
  - pip install .
  - python scripts/deploy.py
```

Runs on push to the default branch. Add rules for other branches/environments as needed.

## Typical workflow (GitLab, no Fabric Git Sync)

Fabric does not support GitLab for native workspace Git Sync. Use `pull` instead:

1. Edit reports/semantic models in Fabric dev workspace.
2. `python scripts/pull.py` → commit → push to GitLab.
3. Merge to main.
4. CI runs `python scripts/deploy.py` → full deploy to target workspace.

## Project structure

```
scripts/deploy.py          # entry: Git → workspace
scripts/pull.py            # entry: workspace → Git
src/powerbi_gitlab/        # deploy + export logic
src/core_api/              # Fabric REST API client
```

## Optional: orphan cleanup

Controlled in `config.yml` under `unpublish` ([Configuration Deployment](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/config_deployment/)). When `unpublish.skip: false`, fabric-cicd removes Report/SemanticModel items in the workspace that are **not in Git**. Other workspace item types are never affected.

## Parameterization

`parameter.yml` at repo root. `config.yml` sets `core.parameter: "parameter.yml"`. fabric-cicd applies it at deploy — see [Parameterization](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/parameterization/).

## Documentation links

### Environment mapping & deploy

- [fabric-cicd Configuration Deployment](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/config_deployment/) — **`config.yml`**, workspace per env, publish/unpublish
- [fabric-cicd Parameterization](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/parameterization/) — `parameter.yml`, `semantic_model_binding`, `find_replace`
- [fabric-cicd Getting Started](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/getting_started/) — auth, directory layout, GIT flow
- [fabric-cicd Code Reference](https://microsoft.github.io/fabric-cicd/0.3.0/code_reference/) — `publish_all_items`, `unpublish_all_orphan_items`
- [fabric-cicd Troubleshooting](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/troubleshooting/)

### Git layout & Fabric platform

- [Git source code format](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format) — `.SemanticModel/`, `.Report/` folder structure
- [Fabric Git integration](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration) — supported providers (GitLab not native)
- [Bulk Export API](https://learn.microsoft.com/en-us/rest/api/fabric/core/items/bulk-export-item-definitions(beta)) — used by `pull.py`

Full list: [docs/REQUIREMENTS.md §14](docs/REQUIREMENTS.md#14-documentation-links)
