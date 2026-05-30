# 🧪 Phase 9 — Hands-On Lab: Test, Containerize, Deploy

> A step-by-step lab. By the end you'll have a unit-tested, Dockerized agent running in **Azure Container Apps** with Application Insights wired up.

---

## 🎯 What you'll build today

You'll take the Phase 6 Knowledge Agent through the full production pipeline:

1. Write **pytest unit tests** using the SDK's `TestAdapter` — no network calls.
2. Test interactively with the **Bot Framework Emulator**.
3. **Containerize** the agent with a `Dockerfile`.
4. **Deploy** to Azure Container Apps with `azd` (Azure Developer CLI).
5. Wire **Application Insights** for production telemetry.
6. Run a few **KQL queries** to spot errors.

> 👶 So far the agent has only run on your laptop. Today we put it into the cloud — properly, with tests and monitoring, like a real production service.

⏱️ **About 150 minutes** (much of it waiting for cloud deployments).

---

## ✅ Before you start

- [ ] Phase 6 finished — `lab_knowledge` works on your laptop.
- [ ] Terminal prompt starts with **`(.venv)`**.
- [ ] **Docker Desktop** installed and running (<https://docs.docker.com/desktop>).
- [ ] **Azure CLI** installed (`az --version`). Install via `winget install Microsoft.AzureCLI`.
- [ ] **Azure Developer CLI** installed (`azd version`). Install via `winget install Microsoft.AzureDeveloperCLI`.
- [ ] An **Azure subscription** you can deploy to.

---

## 🗺️ Today's roadmap

```
Lab 1 → Unit tests with TestAdapter + mocked LLM
Lab 2 → Bot Framework Emulator interactive test
Lab 3 → Dockerfile + local docker run
Lab 4 → Bicep + azure.yaml + azd up
Lab 5 → Application Insights KQL queries
Lab 6 → Production checklist
```

---

## Lab 1 — Unit tests with TestAdapter (~30 min)

### Step 1.1 — Setup

```powershell
cd Phase9_Testing_and_Deployment
mkdir -Force lab_ship
cd lab_ship

# Copy the Phase 6 agent
Copy-Item ..\..\Phase6_Tools_and_RAG\lab_knowledge\*.py .
Copy-Item ..\..\Phase6_Tools_and_RAG\lab_knowledge\.env .
Copy-Item -Recurse ..\..\Phase6_Tools_and_RAG\lab_knowledge\docs .

# Test dependencies
pip install pytest pytest-asyncio
```

### Step 1.2 — Create `tests/test_handlers.py`

```powershell
mkdir -Force tests
New-Item tests\__init__.py -ItemType File
New-Item tests\test_handlers.py -ItemType File
code tests\test_handlers.py
```

Paste:

```python
"""test_handlers.py — exercises the agent without any network."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TestAdapter, TurnContext, TurnState,
)


def make_app():
    app = AgentApplication(storage=MemoryStorage())

    @app.message("ping")
    async def on_ping(context: TurnContext, state: TurnState):
        await context.send_activity("pong")

    @app.activity("message")
    async def echo(context: TurnContext, state: TurnState):
        await context.send_activity(f"You said: {context.activity.text}")

    return app


@pytest.mark.asyncio
async def test_ping_returns_pong():
    app = make_app()
    adapter = TestAdapter()
    await adapter.process_activity_with_message("ping", app)
    reply = adapter.get_next_reply()
    assert reply.text == "pong"


@pytest.mark.asyncio
async def test_echo_for_other_input():
    app = make_app()
    adapter = TestAdapter()
    await adapter.process_activity_with_message("hello world", app)
    reply = adapter.get_next_reply()
    assert reply.text == "You said: hello world"
```

> ⚠️ If `TestAdapter`/`process_activity_with_message` is named differently in your SDK build, run:
>
> ```powershell
> python -c "import microsoft_agents.hosting.core as m; print([n for n in dir(m) if 'Test' in n or 'Adapter' in n])"
> ```
>
> Then adapt the import.

### Step 1.3 — Run

```powershell
pytest -q tests
```

You should see `2 passed`.

### Step 1.4 — Add a mocked LLM test

Add to `tests/test_handlers.py`:

```python
import tools_v3, rag

@pytest.mark.asyncio
async def test_get_weather_tool_dispatches():
    # Direct test of the dispatch table
    assert "get_weather" in tools_v3.DISPATCH
    result = tools_v3.DISPATCH["get_weather"](city="Tokyo")
    assert "22°C" in result or "Tokyo" in result


@pytest.mark.asyncio
async def test_lookup_policy_returns_string_when_no_index():
    # Ensure the RAG store is empty so search returns []
    rag._chunks = []
    rag._vectors = None
    result = tools_v3.DISPATCH["lookup_policy"](question="anything")
    assert "No relevant policy found" in result
```

Run again:

```powershell
pytest -q tests
```

Should see `4 passed`.

### ✅ Checkpoint 1
All tests pass, no network calls.

---

## Lab 2 — Bot Framework Emulator (~20 min)

**You will:** chat with the agent in a real UI.

### Step 2.1 — Install the Emulator

Download the latest from <https://github.com/Microsoft/BotFramework-Emulator/releases>. Install.

### Step 2.2 — Start your agent

In one terminal (in `lab_ship`):

```powershell
# Make sure your .env has ANONYMOUS_ALLOWED=true for local
Add-Content .env "`nANONYMOUS_ALLOWED=true"
python app_v1.py
```

### Step 2.3 — Open the Emulator

Launch **Bot Framework Emulator** → **Open Bot**:

- **Bot URL**: `http://localhost:3978/api/messages`
- **App ID** + **App password**: leave blank
- Click **Connect**

### Step 2.4 — Chat

Type:

```text
What's the weather in Tokyo?
```

You should get a reply. Open the **Inspector** pane on the right — every activity is shown as JSON. You can see the LLM's tool calls coming through.

### ✅ Checkpoint 2
You can chat with the agent through the Emulator and inspect activity JSON.

---

## Lab 3 — Dockerize (~25 min)

### Step 3.1 — Create `Dockerfile`

```powershell
New-Item Dockerfile -ItemType File
code Dockerfile
```

Paste:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy app code
COPY . .

EXPOSE 3978
CMD ["python", "app_v1.py"]
```

### Step 3.2 — Create a minimal `requirements.txt` for this folder

```powershell
@"
microsoft-agents-hosting-core
microsoft-agents-hosting-aiohttp
microsoft-agents-activity
openai
python-dotenv
numpy
httpx
"@ | Out-File requirements.txt -Encoding utf8
```

> 💡 Pin versions in production: `microsoft-agents-hosting-core==1.2.3`. Use `pip freeze > requirements.txt` from a known-good venv.

### Step 3.3 — Make a `.dockerignore`

```powershell
@"
.venv
.git
__pycache__
*.pyc
tests
.env
identity
"@ | Out-File .dockerignore -Encoding utf8
```

> ⚠️ `.env` is excluded because secrets shouldn't be baked into the image. We'll pass them as **runtime env vars** instead.

### Step 3.4 — Build & run

```powershell
docker build -t knowledge-agent:dev .
```

Wait ~2 min. Then:

```powershell
docker run --rm -p 3978:3978 --env-file .env knowledge-agent:dev
```

You should see `Running on http://0.0.0.0:3978`.

### Step 3.5 — Test the running container

In a 2nd terminal:

```powershell
$body = @{ type="message"; text="ping"; from=@{id="u1"}; recipient=@{id="b"}; conversation=@{id="c1"}; serviceUrl="http://localhost" } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages -Method POST -ContentType "application/json" -Body $body
```

Should respond OK. Stop the container with `Ctrl+C`.

### ✅ Checkpoint 3
`docker build` succeeds and `docker run` serves traffic on port 3978.

---

## Lab 4 — Deploy to Azure Container Apps with `azd` (~45 min)

### Step 4.1 — Create the Bicep files

```powershell
mkdir -Force infra
New-Item infra\main.bicep -ItemType File
code infra\main.bicep
```

Paste:

```bicep
@description('Name prefix.')
param namePrefix string = 'agentlab'

@description('Region.')
param location string = resourceGroup().location

@secure()
param azureOpenAiApiKey string
param azureOpenAiEndpoint string
param azureOpenAiDeployment string = 'gpt-4o-mini'
param azureOpenAiEmbeddingDeployment string = 'text-embedding-3-small'

var lawName = '${namePrefix}-law'
var aiName = '${namePrefix}-ai'
var envName = '${namePrefix}-cae'
var appName = '${namePrefix}-app'

resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: lawName
  location: location
  properties: { sku: { name: 'PerGB2018' } }
}

resource ai 'Microsoft.Insights/components@2020-02-02' = {
  name: aiName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: law.id
  }
}

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: listKeys(law.id, '2022-10-01').primarySharedKey
      }
    }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3978
        transport: 'auto'
      }
      secrets: [
        { name: 'aoai-key', value: azureOpenAiApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'agent'
          image: 'mcr.microsoft.com/azuredocs/aci-helloworld'   // placeholder until first deploy
          resources: { cpu: json('0.5'), memory: '1.0Gi' }
          env: [
            { name: 'AZURE_OPENAI_API_KEY', secretRef: 'aoai-key' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
            { name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT', value: azureOpenAiEmbeddingDeployment }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: ai.properties.ConnectionString }
            { name: 'ANONYMOUS_ALLOWED', value: 'true' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 1 }
    }
  }
}

output fqdn string = app.properties.configuration.ingress.fqdn
output appName string = app.name
```

### Step 4.2 — Create `azure.yaml`

```powershell
New-Item azure.yaml -ItemType File
code azure.yaml
```

Paste:

```yaml
name: knowledge-agent-lab
metadata:
  template: bicep@v0.1
infra:
  provider: bicep
  path: infra
  module: main
services:
  agent:
    project: .
    language: py
    host: containerapp
    docker:
      path: Dockerfile
      context: .
```

### Step 4.3 — Login and init

```powershell
az login
azd auth login
azd init --location eastus
```

Pick **No** when asked about a template (we already have Bicep).

### Step 4.4 — Set the Bicep parameters

`azd` will prompt for `azureOpenAiApiKey` and `azureOpenAiEndpoint` on the first run. Have them ready.

### Step 4.5 — Deploy

```powershell
azd up
```

This:

1. Provisions the resource group, Log Analytics, App Insights, Container Apps environment, and Container App.
2. Builds your Docker image and pushes to an internal registry.
3. Updates the Container App to use your image.

Takes ~5–10 min. The final output prints the FQDN:

```text
agent FQDN: agentlab-app.kindsky-…eastus.azurecontainerapps.io
```

### Step 4.6 — Test the deployed agent

```powershell
$fqdn = "https://agentlab-app.kindsky-…eastus.azurecontainerapps.io"
$body = @{ type="message"; text="ping"; from=@{id="u1"}; recipient=@{id="b"}; conversation=@{id="c1"}; serviceUrl="http://localhost" } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "$fqdn/api/messages" -Method POST -ContentType "application/json" -Body $body
```

Returns silently = success. Logs show in App Insights.

### Step 4.7 — Stream container logs

```powershell
az containerapp logs show -n agentlab-app -g rg-knowledge-agent-lab-dev --follow
```

(Resource group name = `rg-<envname>-<envname>`; check `azd env get-values`.)

### ✅ Checkpoint 4
The Container App responds at its public FQDN; logs stream live.

---

## Lab 5 — KQL queries (~15 min)

In Azure portal → your **Application Insights** → **Logs**.

Try each:

### Top errors in the last hour

```kusto
traces
| where timestamp > ago(1h) and severityLevel >= 3
| project timestamp, message, severityLevel
| order by timestamp desc
| take 50
```

### Request volume per minute

```kusto
requests
| where timestamp > ago(1h)
| summarize count() by bin(timestamp, 1m)
| render timechart
```

### p95 latency per route

```kusto
requests
| where timestamp > ago(1h)
| summarize p95=percentile(duration, 95) by name
| order by p95 desc
```

### Outgoing OpenAI calls

```kusto
dependencies
| where target contains "openai"
| project timestamp, duration, success, name
| order by timestamp desc
| take 50
```

### ✅ Checkpoint 5
At least one query returns data (the agent has been hit enough times).

---

## Lab 6 — Production checklist (~5 min)

Tick before you call any agent "production-ready":

- [ ] No secrets in code or git — use Container Apps **secrets** or Key Vault.
- [ ] `MICROSOFT_APP_ID / PASSWORD / TENANT_ID` set for the real Bot resource.
- [ ] `ANONYMOUS_ALLOWED=false` (or remove the var) once Bot Service auth is on.
- [ ] **HTTPS only** — Container Apps default ingress is HTTPS, never disable it.
- [ ] App Insights wired and a few queries verified.
- [ ] **pytest** suite passes in CI.
- [ ] **Health endpoint**: add `/healthz` returning 200 for the platform to probe.
- [ ] **Rate limit / retry** on outbound OpenAI calls.
- [ ] **Min replicas ≥ 1** (so cold starts don't bite users).

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| `pytest` errors `cannot import name TestAdapter` | SDK build doesn't export it from `microsoft_agents.hosting.core`. | Try `from microsoft_agents.hosting.core.testing import TestAdapter`. Or grep with `python -c "import microsoft_agents.hosting.core as m; print(dir(m))"`. |
| `docker build` fails on `pip install` | Wrong base image or proxy issues. | Set `--network=host`; pin `python:3.11-slim`; if behind proxy, pass `--build-arg HTTP_PROXY=...`. |
| `azd up` says quota exceeded | Subscription quota too small for the SKU. | Pick a smaller region or request a quota increase. |
| Container Apps shows `Provisioning failed: invalid image` | Image push failed or wrong registry. | Re-run `azd deploy`; check `az acr repository list`. |
| App responds but App Insights is empty | Connection string is wrong in container env. | `az containerapp env-vars list -n agentlab-app -g rg-...` to confirm. |
| Cold start ~30s | Min replicas = 0. | Set `minReplicas: 1` in the Bicep. |
| `403 Forbidden` from Azure CLI | Not logged in or wrong subscription. | `az account set --subscription <id>`. |

---

## 🎓 Self-check

1. **What's the difference between a unit test and an Emulator test?**

   <details><summary>Show answer</summary>
   Unit tests run the handler in-process with `TestAdapter`, no network, fast (ms). Emulator tests drive the real HTTP endpoint with a UI — slower, but useful for manually inspecting activity JSON.
   </details>

2. **Why do we exclude `.env` in `.dockerignore`?**

   <details><summary>Show answer</summary>
   So secrets never get baked into the image. Pass them as runtime env vars (Container Apps secrets, Key Vault references, etc.).
   </details>

3. **What does `azd up` do under the hood?**

   <details><summary>Show answer</summary>
   `azd provision` (deploys the Bicep) + `azd deploy` (builds your Docker image, pushes it, updates the Container App).
   </details>

4. **Which KQL query would you run to find the slowest 10 requests?**

   <details><summary>Show answer</summary>

   ```kusto
   requests | order by duration desc | take 10
   ```

   </details>

5. **Why set `minReplicas: 1`?**

   <details><summary>Show answer</summary>
   So there's always one warm container ready to serve. With `0`, the first user after an idle period waits for a cold start (~30 sec).
   </details>

---

## 🚀 Bonus tasks

1. **GitHub Action** — `.github/workflows/ci.yml` that runs `pytest` on every push.
2. **Auto-deploy on main** — extend the action with `azd up` on push to `main` (needs federated credentials).
3. **Health endpoint** — add `/healthz` to `app_v1.py` returning `{"status": "ok"}`.
4. **Blue/green** — deploy 2 revisions of the Container App and split traffic 90/10.
5. **Cost dashboard** — Azure Monitor Workbook showing tokens, requests, and OpenAI spend per hour.

---

## 🏁 You're done!

You can now:

- Unit-test handlers with `TestAdapter` and mock the LLM.
- Test interactively with the Bot Framework Emulator.
- Containerize with a Dockerfile.
- Deploy to Azure Container Apps with `azd up`.
- Read production traces and metrics in App Insights with KQL.

Next → [Phase 10 — Capstone: Contoso IT Companion](../Phase10_Capstone/README.md)
