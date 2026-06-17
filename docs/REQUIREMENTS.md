# Power BI GitLab CI/CD — Requirements & Architecture

> **Status:** Implemented (MVP)  
> **Base library:** [fabric-cicd](https://microsoft.github.io/fabric-cicd/0.3.0/) v1.1.0  
> **Project:** `powerbi-gitlab`  
> **Scope:** Power BI **Reports** and **Semantic Models** only

---

## 1. Summary

This project deploys and syncs **Power BI Reports** and **Semantic Models** between **GitLab** and **Microsoft Fabric**.

| Direction | Mechanism | Entry point |
|-----------|-----------|-------------|
| **Git → workspace** | fabric-cicd `deploy_with_config` + `config.yml` | `python scripts/deploy.py` (GitLab CI) |
| **Workspace → Git** | Fabric Bulk Export API via `core_api` | `python scripts/pull.py` (developer machine) |

**Design principles (as built):**

- GitLab YAML defines **when** to deploy (branch rules, variables).
- Python scripts contain **how** to deploy or pull.
- No custom CLI package — plain `python scripts/*.py`.
- CI does **not** check whether pull was run; **Git wins** on deploy and overwrites the workspace.
- Single deploy job on default branch (extend rules as needed).

---

## 2. Scope

| In scope | Out of scope |
|----------|--------------|
| `Report` | Notebooks, pipelines, lakehouses, warehouses, etc. |
| `SemanticModel` | Other fabric-cicd item types |

`item_types_in_scope` is set in `config.yml` (`Report`, `SemanticModel`).

`unpublish_all_orphan_items` (optional, `--unpublish-orphans`) only removes **Report** and **SemanticModel** items that exist in the workspace but not in Git. Other workspace items are never touched.

---

## 3. Repository layout (implemented)

```
powerbi_gitlab/
├── scripts/
│   ├── deploy.py              # CI + local: Git → workspace
│   └── pull.py                # Local: workspace → Git
├── src/
│   ├── powerbi_gitlab/
│   │   ├── constants.py       # ASSETS_DIR, ITEM_TYPES, FABRIC_API_ROOT
│   │   ├── fabric_export.py   # list_items, export_items, write_files
│   │   ├── pull.py            # pull_workspace(client, ...)
│   │   ├── sync.py            # sync_workspace(client, ...) + git
│   │   ├── deploy.py          # deploy_workspace(config, env)
│   │   └── auth_builders.py   # optional auth for scripts/tests
│   └── core_api/
│       ├── api/fabric.py      # Fabric REST client (LRO, pagination, 429)
│       └── auth/
│           └── fabric_service_principal.py
├── config.yml                 # fabric-cicd deploy config (workspace per env)
├── .gitlab-ci.yml
├── docs/REQUIREMENTS.md
├── pyproject.toml
└── README.md

# Power BI content (same repo or separate — see §5)
asset/
├── Sales.Report/
├── Sales.SemanticModel/
config.yml / parameter.yml (repo root)
```

---

## 4. `content_path` / `repository_directory`

fabric-cicd's `repository_directory` is a **local folder on disk**, not a Git URL.

It must contain Git-integration-style trees:

```
content_path/
├── Sales.Report/
│   ├── .platform
│   └── definition.pbir
├── Sales.SemanticModel/
│   ├── .platform
│   └── definition.pbism
└── parameter.yml
```

| Context | `repository_directory` in `config.yml` |
|---------|----------------------------------------|
| GitLab CI | `.` (repo root is `CI_PROJECT_DIR`) |
| Local | `.` or change `core.repository_directory` in `config.yml` |

If tooling and Power BI content live in **different repos**, set `core.repository_directory` in `config.yml` (or clone the content repo into the path it points at before deploy).

---

## 5. GitLab and Fabric Git integration

Microsoft Fabric native Git Sync supports **GitHub and Azure DevOps only** — not GitLab ([Learn docs](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration)).

### Adapted workflow (no mirror)

```
Edit in Fabric (dev workspace, no Git Sync)
        ↓
python scripts/pull.py          # workspace → local files
        ↓
git commit / push → GitLab
        ↓
merge to main
        ↓
GitLab CI: python scripts/deploy.py   # Git → workspace (full deploy)
```

### fabric-cicd GIT flow (reference)

From [Getting Started — GIT Flow](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/getting_started/):

1. **Deployed branches** are **not** connected to workspaces via Git Sync.
2. **Feature branches** are connected via Git Sync (GitHub/ADO only — we use `pull` instead).
3. **Deployed workspaces** are updated **only** through script deployment.
4. Feature branches merge to deployed branch; cherry-pick to upper envs (optional).
5. **Full deployment** every run — no commit diffs.

---

## 6. Scripts

### 6.1 Deploy — `scripts/deploy.py` + `config.yml`

Uses [Configuration Deployment](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/config_deployment/):

```python
deploy_with_config(config_file_path="config.yml", environment="PROD")
```

`config.yml` defines per environment:

- `core.workspace_id` — `DEV` / `PPE` / `PROD` from `$ENV:FABRIC_WORKSPACE_ID_DEV` etc. (requires `enable_environment_variable_replacement`)
- `core.repository_directory` — local folder with item trees (default `.`)
- `core.item_types_in_scope` — `Report`, `SemanticModel`
- `core.parameter` — path to `parameter.yml`
- `publish.skip` / `unpublish.skip` — control publish and orphan cleanup per env

**Authentication:** `DefaultAzureCredential` via fabric-cicd (CI: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`).

| Argument / env | Purpose |
|----------------|---------|
| `--config` / `FABRIC_CONFIG` | Path to `config.yml` |
| `--environment` / `FABRIC_ENVIRONMENT` | `DEV`, `PPE`, or `PROD` |
| `FABRIC_WORKSPACE_ID_DEV` / `_PPE` / `_PROD` | Workspace GUIDs (`$ENV:FABRIC_WORKSPACE_ID_*` in `config.yml`) |
| `FABRIC_CONNECTION_ID_DEV` / `_PPE` / `_PROD` | Connection GUIDs (`$ENV:FABRIC_CONNECTION_ID_*` in `parameter.yml`) |
| `--debug` | fabric-cicd debug logging |

### 6.2 Pull — `scripts/pull.py`

Uses `core_api` + [Bulk Export Item Definitions (beta)](https://learn.microsoft.com/en-us/rest/api/fabric/core/items/bulk-export-item-definitions(beta)):

1. List workspace items → filter `Report`, `SemanticModel`
2. `bulkExportDefinitions` (selective mode)
3. Write decoded files to `--output`
4. Optional `--git-branch` → create branch, commit, print merge instructions

**Authentication:** service principal via env vars (see §7).

| Argument / env | Purpose |
|----------------|---------|
| `--workspace-id` / `FABRIC_WORKSPACE_ID` | Source workspace |
| `--output` | Write directory (default `.`) |
| `--git-branch` | Create `sync/workspace-<timestamp>` and commit |

### 6.3 `unpublish_all_orphan_items`

Optional second step after publish. Removes **orphan** Report/SemanticModel items in the workspace — items that exist in Fabric but have **no matching folder** in `content_path`.

- **Off by default** in CI.
- Use when Git is the single source of truth and deleted repo items should disappear from the workspace.
- Does not affect notebooks, lakehouses, or other item types.

---

## 7. Authentication

| Script | Method | Setup |
|--------|--------|-------|
| **deploy** | `DefaultAzureCredential` (fabric-cicd) | CI: `AZURE_*` service principal — local: `az login` |
| **pull** | Service principal (`core_api`) | `MS_*` env vars or `.env` |

### Deploy (GitLab CI)

Set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` in CI/CD variables. fabric-cicd picks them up automatically — no `az login`.

### Deploy (local)

```bash
az login
python scripts/deploy.py
```

### Pull (local / automation)

| Variable | Required | Notes |
|----------|----------|-------|
| `MS_CLIENT_ID` | Yes | App registration |
| `MS_CLIENT_SECRET` | Yes | Client secret |
| `MS_TENANT_ID` | Yes | Azure tenant |
| `MS_FABRIC_SCOPE` | No | **Array** — JSON `["https://api.fabric.microsoft.com/.default"]`, comma-separated, or space-separated. Default: `["https://api.fabric.microsoft.com/.default"]` |

Parsed by `parse_fabric_scopes()` in `core_api/auth/scopes.py`.

---

## 8. GitLab CI (implemented)

```yaml
# .gitlab-ci.yml
deploy:fabric:
  image: python:3.12-slim
  script:
    - pip install .
    - python scripts/deploy.py
```

| Variable | Purpose |
|----------|---------|
| `AZURE_CLIENT_ID` | Service principal client ID |
| `AZURE_CLIENT_SECRET` | Service principal secret (masked) |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `FABRIC_CONFIG` | Path to `config.yml` |
| `FABRIC_ENVIRONMENT` | `DEV`, `PPE`, or `PROD` |
| `FABRIC_WORKSPACE_ID_DEV` / `_PPE` / `_PROD` | Workspace GUIDs (`$ENV:FABRIC_WORKSPACE_ID_*` in `config.yml`) |
| `FABRIC_CONNECTION_ID_DEV` / `_PPE` / `_PROD` | Connection GUIDs (`$ENV:FABRIC_CONNECTION_ID_*` in `parameter.yml`) |

**No sync check in CI.** Whatever is in Git at pipeline time is deployed. If Fabric was edited but `pull` was not run, **deploy overwrites** the workspace with Git content.

---

## 9. Developer workflow

### Content changed in Fabric

```bash
python scripts/pull.py --workspace-id $DEV_WORKSPACE_ID --output .

# Optional: sync branch + merge
python scripts/pull.py --workspace-id $DEV_WORKSPACE_ID --git-branch
git checkout feature/my-branch
git merge sync/workspace-20250608-120000
# resolve conflicts, commit, push
```

### Deploy after merge to main

Automatic via GitLab CI on default branch.

### Local deploy test

```bash
az login
pip install .
python scripts/deploy.py --environment PPE
```

---

## 10. Feature → prod: how semantic models are mapped

Git carries the **model definition** (TMDL / `.SemanticModel/` files). It does **not** carry per-environment connection IDs. Mapping across environments is done in **`parameter.yml`** at deploy time.

| What | Carried by | Doc |
|------|------------|-----|
| Model schema, measures, relationships | Git (same on all branches after merge) | [Git source code format — Semantic model files](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format) |
| Connection / gateway per environment | `parameter.yml` → `semantic_model_binding` | [fabric-cicd Parameterization — semantic_model_binding](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/parameterization/) |
| Which environment key to apply | `FABRIC_ENVIRONMENT` / `--environment` | [fabric-cicd Getting Started](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/getting_started/) |
| Deployed branch → workspace (no Git Sync) | CI `scripts/deploy.py` | [fabric-cicd GIT Flow](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/getting_started/) |

### Flow

```
feature branch (Git)  →  merge to main  →  CI deploy with FABRIC_ENVIRONMENT=PROD
                                                    ↓
                              publish_all_items (full deploy from Git)
                                                    ↓
                              parameter.yml applies PROD connection bindings
```

### `parameter.yml`

Repo root. `config.yml` → `core.parameter`. Structure per [fabric-cicd Parameterization](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/parameterization/) (`semantic_model_binding` recommended format). Environment keys must match `FABRIC_ENVIRONMENT`.

**Limitation:** only **one** connection per semantic model via `semantic_model_binding`; additional connections must be configured manually in the target workspace ([Parameterization notes](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/parameterization/)).

---

## 11. Implementation status

### Done

- [x] `config.yml` + `scripts/deploy.py` — `deploy_with_config` (Report + SemanticModel)
- [x] `scripts/pull.py` — Bulk Export via `core_api`
- [x] `core_api` — Fabric API client (LRO, pagination, throttling)
- [x] Service principal auth for pull with scope array
- [x] Deploy auth via `DefaultAzureCredential` (`AZURE_*` in CI, `az login` local)
- [x] `.gitlab-ci.yml` — single deploy on default branch
- [x] Unpublish orphans configurable in `config.yml` (`unpublish.skip` per env)
- [x] `parameter.yml` per fabric-cicd parameterization docs
- [x] Optional `--git-branch` on pull

### Not implemented (future)

- [ ] `validate` script / pre-commit hooks
- [ ] Multi-branch CI rules (develop / PPE / PROD)
- [ ] MR validation pipeline
- [ ] `item_name_exclude_regex` for unpublish

---

## 12. Open decisions

1. **Orphan cleanup** — Enable `--unpublish-orphans` in CI for PROD only, or never?
2. **Repo layout** — Power BI content in same GitLab repo as scripts, or separate repo?
3. **Branch rules** — Single default-branch deploy vs per-environment branches?
4. **Mixed workspace** — Confirm leaving non–Power BI items untouched during unpublish is acceptable.

---

## 13. Glossary

| Term | Meaning |
|------|---------|
| **content_path** | Local folder passed to fabric-cicd as `repository_directory` |
| **Full deployment** | Every run publishes all in-scope items; no commit-diff optimization |
| **Orphan** | Report/SemanticModel in workspace but missing from `content_path` |
| **Deployed branch** | Branch that triggers CI deploy (e.g. `main`); no Fabric Git Sync |
| **pull** | Export workspace definitions to Git-format files on disk |

---

## 14. Documentation links

### fabric-cicd (deploy)

| Topic | Link |
|-------|------|
| Overview | [fabric-cicd Home](https://microsoft.github.io/fabric-cicd/0.3.0/) |
| **`config.yml` deployment** | [Configuration Deployment](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/config_deployment/) |
| Authentication (`az login`, DefaultAzureCredential) | [Getting Started — Authentication](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/getting_started/) |
| GIT flow (deployed branches, full deploy) | [Getting Started — GIT Flow](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/getting_started/) |
| `repository_directory` / folder layout | [Getting Started — Directory Structure](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/getting_started/) |
| **`parameter.yml` / semantic model mapping** | [Parameterization](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/parameterization/) |
| `semantic_model_binding` | [Parameterization — semantic_model_binding](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/parameterization/) |
| `publish_all_items` / `unpublish_all_orphan_items` | [Code Reference](https://microsoft.github.io/fabric-cicd/0.3.0/code_reference/) |
| Troubleshooting / debug logs | [Troubleshooting](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/troubleshooting/) |

### Microsoft Fabric (Git integration & APIs)

| Topic | Link |
|-------|------|
| Supported Git providers (GitLab not supported) | [Git integration overview](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration) |
| Semantic model / report folder layout in Git | [Git source code format](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format) |
| Get started with Fabric Git | [Git integration get started](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-get-started) |
| **Bulk export** (used by `pull.py`) | [Bulk Export Item Definitions (beta)](https://learn.microsoft.com/en-us/rest/api/fabric/core/items/bulk-export-item-definitions(beta)) |
| Bulk import / export overview | [Public APIs blog — bulk import/export](https://blog.fabric.microsoft.com/en-US/blog/public-apis-bulk-import-and-export-items-definition-preview/) |
