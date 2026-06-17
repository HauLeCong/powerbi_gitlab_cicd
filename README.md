# powerbi-gitlab

Deploy and pull **Power BI Reports** and **Semantic Models** between **GitLab** / **GitHub** and **Microsoft Fabric**.

See [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for architecture and design decisions.

## Prerequisites

- Python **3.12**, [Poetry](https://python.poetry.org/)
- Fabric workspace access (Admin or Member)
- A **service principal** for CI (see below) or `az login` for local deploy only

---

## Azure service principal (Entra ID)

**Required for GitLab/GitHub CI.** Complete all six steps before running pipelines.

### 1. Create app registration (Entra ID)

1. Open [Microsoft Entra admin center](https://entra.microsoft.com/) → **Identity** → **Applications** → **App registrations**.
2. **New registration** → name (e.g. `powerbi-gitlab-cicd`) → single tenant → **Register**.
3. On **Overview**, copy:

| Entra field | Variable |
|-------------|----------|
| **Application (client) ID** | `AZURE_CLIENT_ID` / `MS_CLIENT_ID` |
| **Directory (tenant) ID** | `AZURE_TENANT_ID` / `MS_TENANT_ID` |

### 2. Create client secret

1. App → **Certificates & secrets** → **Client secrets** → **New client secret**.
2. Copy the **Value** immediately (shown once) → `AZURE_CLIENT_SECRET` / `MS_CLIENT_SECRET`.
3. Never commit secrets; use GitLab/GitHub CI variables or `tests/.test.env`.

### 3. API permissions

1. App → **API permissions** → **Add a permission**.
2. **APIs my organization uses** → **Microsoft Fabric** and/or **Power BI Service**.
3. Choose **Application permissions** (not Delegated). Add read/write permissions for workspace items (e.g. `Workspace.ReadWrite.All`, `Item.ReadWrite.All` — exact names depend on tenant).
4. Click **Grant admin consent for [tenant]** (Entra admin required).

### 4. Fabric / Power BI admin tenant setting

1. Open [Fabric admin portal](https://app.fabric.microsoft.com/admin-portal).
2. **Tenant settings** → **Developer settings** (or **Admin API settings**).
3. Enable:
   - **Service principals can use Fabric APIs**
   - **Allow service principals to use Power BI APIs** (if shown separately)
4. Apply to the whole organization or a security group that includes this app.

If this is disabled, login works but deploy/pull API calls fail.

### 5. Add the service principal to each Fabric workspace

Repeat for **DEV**, **PPE**, and **PROD** workspaces (GUIDs in `config.yml`):

1. In Fabric, open the workspace → **Manage access** (or workspace settings → access).
2. **Add people or groups**.
3. Search for the **app registration name** (service principal — not the secret string).
4. Assign **Admin** or **Member** (use **Admin** if PROD unpublish is enabled).

The service principal must appear in the workspace access list before deploy or pull can succeed.

### 6. Wire credentials to this repo

| Use case | Variables |
|----------|-----------|
| GitLab / GitHub CI deploy | `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` |
| Local deploy | Same `AZURE_*`, or `az login` |
| Local pull (default) | `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT_ID` (same app) |
| Tests | `tests/.test.env` — `AZURE_*` + `FABRIC_WORKSPACE_ID` |

**GitLab / GitHub CI:** Settings → CI/CD → Variables. Mask the secret; turn **off** “Expand variable reference” on the secret.

**Verify token locally:**

```bash
export AZURE_CLIENT_ID=... AZURE_CLIENT_SECRET=... AZURE_TENANT_ID=...
poetry run python -c "from azure.identity import DefaultAzureCredential; print('OK', len(DefaultAzureCredential().get_token('https://api.fabric.microsoft.com/.default').token))"
```

---

## First-time setup

```bash
git clone <repo-url>
cd powerbi_gitlab
poetry install
```

### Configure `config.yml`

Edit workspace GUIDs directly (from Fabric portal URL):

```yaml
core:
  repository_directory: "asset"
  workspace_id:
    DEV: "<dev-workspace-guid>"
    PPE: "<ppe-workspace-guid>"
    PROD: "<prod-workspace-guid>"
```

### Content in `asset/`

```
asset/
├── My Report.Report/
│   ├── definition.pbir    # use byPath → ../My Report.SemanticModel
│   └── ...
└── My Report.SemanticModel/
    └── ...
```

---

## Run locally

### Deploy (Git → Fabric)

```bash
poetry run python scripts/deploy.py --environment DEV
```

| Flag | Env variable | Default |
|------|--------------|---------|
| `--environment` | `FABRIC_ENVIRONMENT` | `PROD` |
| `--config` | `FABRIC_CONFIG` | `config.yml` |
| `--git-compare-ref` | `FABRIC_GIT_COMPARE_REF` | `main` |

### Pull (Fabric → Git)

```bash
export MS_CLIENT_ID=... MS_CLIENT_SECRET=... MS_TENANT_ID=...
poetry run python scripts/pull.py --workspace-id "<workspace-guid>"
```

---

## Required CI/CD variables

| Variable | Required | Notes |
|----------|----------|-------|
| `AZURE_CLIENT_ID` | Yes | From Entra app registration |
| `AZURE_CLIENT_SECRET` | Yes | Masked; no variable expansion |
| `AZURE_TENANT_ID` | Yes | Directory (tenant) ID |

Workspace GUIDs live in **`config.yml`**, not in CI variables. `FABRIC_ENVIRONMENT` is set by `.gitlab-ci.yml` (MR → DEV, `main` → PPE, tag → PROD).

---

## GitLab CI

- Stages: **build** (Docker image) → **deploy**
- First run: ensure Container registry is on; run **`build:image`** once if deploy image is missing
- See [docs/REQUIREMENTS.md §8](docs/REQUIREMENTS.md#8-gitlab-ci-implemented) for promotion rules

---

## Documentation links

- [Register an app in Entra ID](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)
- [Fabric admin — developer settings](https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-developer)
- [fabric-cicd Getting Started](https://microsoft.github.io/fabric-cicd/0.3.0/how_to/getting_started/)
- [Fabric Git source code format](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format)

Full list: [docs/REQUIREMENTS.md §14](docs/REQUIREMENTS.md#14-documentation-links)

## License

MIT — see [LICENSE](LICENSE).
