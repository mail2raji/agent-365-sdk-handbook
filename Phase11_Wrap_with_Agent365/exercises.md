# 🧪 Phase 11 — Hands-On Lab: Wrap Your Agent with Agent 365

> A step-by-step lab. By the end you'll have a tiny "hello world" agent that has been **wrapped** by the Microsoft Agent 365 SDK so it shows up in the **M365 Admin Center → Agents**, streams traces to the **Agent 365 Control Panel**, and is visible in **Microsoft Defender XDR → Advanced Hunting**.

> ℹ️ The Phase 11 [README](README.md) is also a long-form lab. This file is the **step-by-step checklist** version — same outcome, easier to follow, with extra "What just happened?" explanations.

---

## 🎯 What you'll build today

A wrapped agent that has:

1. A tenant **agent identity** (a real Entra app + service principal).
2. A **blueprint** an admin can approve so every tenant user can chat with it.
3. **OpenTelemetry traces** flowing into the **Agent 365 Control Panel**.
4. Rows appearing in **Microsoft Defender XDR → Advanced Hunting** (`CloudAppEvents`, filtered by your agent's app id).

> 👶 Think of it like adopting a pet. The bare agent is the puppy. Agent 365 is the vet visit + microchip + name tag that lets the puppy walk around the office without anyone asking "who let this dog in?"

⏱️ **About 2 hours** end-to-end (most of which is waiting for Azure).

---

## ✅ Before you start (checklist)

- [ ] You've at least skimmed the [Phase 11 README](README.md) so you understand the big picture.
- [ ] PowerShell 7 (Windows) or bash/zsh (Mac/Linux).
- [ ] **VS Code** installed.
- [ ] **Python 3.10 or 3.11** — `python --version`.
- [ ] **.NET 8 SDK** — `dotnet --version`.
- [ ] **Azure CLI** — `az --version`.
- [ ] An **Azure subscription** where you have Contributor on at least one resource group.
- [ ] An **M365 tenant** in the **Frontier preview program** and an **Agent ID Developer** Entra role for your account.

If any box is unchecked, install/request that first and come back.

---

## 🗺️ Today's roadmap

```
Lab 1 → Build & test the bare hello-world agent locally
Lab 2 → Install Agent 365 CLI + Azure CLI login
Lab 3 → Dry-run, then run `a365 setup all`
Lab 4 → Customize the Teams manifest + `a365 publish`
Lab 5 → Deploy the code with `a365 deploy`
Lab 6 → Wire the Teams blueprint Notification URL
Lab 7 → Request + approve a Teams instance, first chat
Lab 8 → Add Agent 365 observability
Lab 9 → Validate in Admin Center, Control Panel, Defender XDR
Lab 10 → Cleanup
```

---

## Lab 1 — Build the bare agent locally (~20 min)

**You will:** create a 30-line "echo" agent and prove it works in the Microsoft 365 Agents Playground.

### Step 1.1 — Create the project folder

```powershell
cd $HOME
mkdir my-first-a365-agent
cd my-first-a365-agent
code .
```

**What just happened?** You made a brand-new empty folder and opened it in VS Code. Every command from now on runs inside this folder.

### Step 1.2 — Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux: `source .venv/bin/activate`.

**What just happened?** You built a private cupboard (`.venv`) for this project's Python packages. Your prompt now starts with `(.venv)`. Without this, every `pip install` could pollute your system Python.

### Step 1.3 — Install the SDK packages

Create `requirements.txt`:

```text
microsoft-agents-hosting-aiohttp
microsoft-agents-hosting-core
microsoft-agents-activity
python-dotenv
```

Then run:

```powershell
pip install -r requirements.txt
```

**What just happened?** You downloaded the 4 packages that make up the M365 Agents SDK building blocks. The `aiohttp` one is the web server; `core` has `AgentApplication`, storage, and state; `activity` has the Teams/Bot data types; `python-dotenv` loads `.env` files.

### Step 1.4 — Create `app.py`

```powershell
New-Item app.py -ItemType File
code app.py
```

Paste:

```python
"""Tiny Hello-World agent. Phase 11 starter."""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from aiohttp import web

from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hello-a365")

AGENT_APP = AgentApplication(storage=MemoryStorage())


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "👋 Hi! I am your first Agent 365 agent. Say anything and I will echo it."
            )


@AGENT_APP.activity("message")
async def echo(context: TurnContext, state: TurnState):
    user_text = context.activity.text or ""
    await context.send_activity(f"You said: {user_text}")


def main() -> None:
    adapter = CloudAdapter()

    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, AGENT_APP)

    async def healthz(_req: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/healthz", healthz)
    port = int(os.environ.get("PORT", 3978))
    log.info("Listening on http://localhost:%s/api/messages", port)
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
```

**What just happened?** This is the simplest possible agent — a 50-line web server that listens on `http://localhost:3978`. It greets new users (`membersAdded`) and echoes whatever they type. The `/healthz` endpoint is for the cloud platform to check the agent is alive.

### Step 1.5 — Create `.env`

```dotenv
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED=True
PORT=3978
```

**What just happened?** The long env var name tells the SDK "for local testing, accept messages without authentication". Don't use this in production — only for the Playground and Bot Framework Emulator.

### Step 1.6 — Run the agent

```powershell
python app.py
```

You should see:

```text
INFO:hello-a365:Listening on http://localhost:3978/api/messages
```

Leave it running.

### Step 1.7 — Test in the Playground

1. Install the **Microsoft 365 Agents Playground** VS Code extension.
2. Press `Ctrl+Shift+P` → `Agents: Open Playground` → choose `http://localhost:3978/api/messages`.
3. Type `hello`.

You should see **"You said: hello"**.

**What just happened?** The Playground is a tiny chat UI that speaks the Bot Framework protocol. It sends your message to `/api/messages`, the SDK routes it to your `echo` handler, and the handler's reply appears back in the UI.

### ✅ Checkpoint 1

- Terminal prints `Listening on http://localhost:3978/api/messages`.
- Playground responds to `hello` with `You said: hello`.

Stop the agent (`Ctrl+C`) before moving on.

---

## Lab 2 — Install the Agent 365 CLI + sign in (~10 min)

**You will:** install the `a365` CLI from Microsoft and log in to Azure.

### Step 2.1 — Confirm .NET is installed

```powershell
dotnet --version
```

You need 8.x or newer.

**What just happened?** The Agent 365 CLI (`a365`) is built on .NET, so .NET 8 must be on your PATH before you install it.

### Step 2.2 — Install the CLI as a global tool

```powershell
dotnet tool install --global Microsoft.Agents.A365.DevTools.Cli --prerelease
```

If you already have it: `dotnet tool update --global Microsoft.Agents.A365.DevTools.Cli --prerelease`.

**What just happened?** `dotnet tool install --global` puts the `a365` command on your PATH. You can now run `a365` from any folder.

### Step 2.3 — Verify the CLI works

```powershell
a365 -h
```

You should see help text listing `setup`, `publish`, `deploy`, `cleanup`.

**What just happened?** If `a365` is found, the install worked. If you get "command not found", open a new terminal so the PATH change is picked up.

### Step 2.4 — Sign in to Azure

```powershell
az login --allow-no-subscriptions
```

A browser opens — pick the **work account** for the M365 tenant you'll provision into.

**What just happened?** The `a365` CLI uses your `az` login under the hood — no separate sign-in. `--allow-no-subscriptions` lets you login even if your account isn't bound to a subscription (some Agent 365 paths don't need one).

### Step 2.5 — Confirm you're in the right tenant

```powershell
az account show --query "{user:user.name, tenantId:tenantId}" -o json
```

**What just happened?** Always double-check. The CLI provisions things in the tenant `az` is currently pointing at — so if you have multiple, switch with `az account set --subscription <id>` before continuing.

### ✅ Checkpoint 2

- `dotnet --version` ≥ 8.x.
- `a365 -h` shows the help screen.
- `az account show` displays your **work** account and the **correct** tenant id.

---

## Lab 3 — Dry-run, then run `a365 setup all` (~25 min)

**You will:** ask the CLI to provision everything Agent 365 needs (resource group, web app, managed identity, Entra blueprint, agent identity, permission grants).

### Step 3.1 — Dry-run first

```powershell
a365 setup all --agent-name <your-initials>-first-agent --dry-run
```

(Replace `<your-initials>` with e.g. `jd`, so the agent name is globally unique.)

**What just happened?** A dry-run shows what `setup all` **would** do without actually creating anything. Treat it like `terraform plan` — you read the table, confirm it's what you want, **then** run for real.

### Step 3.2 — Inspect the planned resources

The output is a table showing:

- The Azure **Resource Group** name.
- The **Web App** name and host.
- The **Managed Identity** name.
- The **Entra Blueprint** display name.
- The **Agent Identity** (app + service principal).
- The **Permission Grants** the CLI will request.

**What just happened?** This is your one chance to catch a typo before resources are real. Names that don't fit Azure rules (e.g. too long, special chars) are caught here.

### Step 3.3 — Run for real

```powershell
a365 setup all --agent-name <your-initials>-first-agent
```

It prints numbered progress: `[1/5] Creating resource group…`, `[2/5] Creating web app…`, etc.

⏰ **5–10 minutes.** Coffee break.

**What just happened?** The CLI ran all 5 provisioning steps. If you have admin rights in the tenant, it also grants the required permission consents. If you don't, it prints PowerShell you can give to your Global Admin.

### Step 3.4 — Save the summary

When it finishes, the CLI prints a **Setup Summary** table. Note these four values (they're also written to `a365.generated.config.json`):

| Field | Where it lives in JSON |
|---|---|
| Agent Blueprint ID | `agentBlueprintId` |
| Agent Identity App ID | `agentIdentity.appId` |
| Messaging Endpoint | `messagingEndpoint` |
| Web App URL | `webAppUrl` |

**What just happened?** Every later command (`a365 publish`, `a365 deploy`) reads `a365.generated.config.json` to know which resources to talk to. **Don't delete this file.**

### ✅ Checkpoint 3

- `Setup completed successfully` printed.
- `a365.generated.config.json` exists in your project root.
- In the Azure portal, the resource group + web app exist.
- **Permission Grants: granted** ✅ — or you've handed the printed script to your admin.

---

## Lab 4 — Customize manifest + `a365 publish` (~10 min)

**You will:** edit the Teams manifest with your name/description and publish it to the M365 admin center.

### Step 4.1 — Open the manifest

The CLI created a folder `manifest/` with `manifest.json` and placeholder icons.

```powershell
code manifest\manifest.json
```

### Step 4.2 — Set the required fields

At minimum, edit:

| Field | Set to |
|---|---|
| `name.short` | Friendly name ≤ 30 chars, e.g. `My First A365 Agent` |
| `name.full` | Longer name |
| `description.short` | One sentence ≤ 80 chars |
| `description.full` | A paragraph describing what the agent does |
| `developer.name` | Your name or org |
| `developer.websiteUrl` | Real URL (your GitHub profile is fine) |
| `developer.privacyUrl` | Real URL |
| `developer.termsOfUseUrl` | Real URL |
| `accentColor` | Hex color, e.g. `#5b53ff` |

> ⚠️ **Do not touch** the `id` or `agenticUserTemplates[].id` fields. `a365 publish` fills those in.

**What just happened?** These fields show up in Teams and the admin center, so other people see them. The four URLs must be real — Teams refuses to install apps with placeholder URLs.

### Step 4.3 — Replace the placeholder icons

Put a 192×192 PNG at `manifest/color.png` and a 32×32 transparent PNG at `manifest/outline.png`.

**What just happened?** Teams needs both icons. Without them the install fails with a confusing schema error.

### Step 4.4 — Publish

```powershell
a365 publish
```

You should see `Publish completed successfully`.

**What just happened?** The CLI uploaded the manifest to your tenant catalog. The agent now exists as a "blueprint" in Microsoft 365 — but it has no code yet. We'll deploy the code next.

### ✅ Checkpoint 4

- `manifest.json` has real `developer` URLs and a real `name.short`.
- Two PNG icons are in `manifest/`.
- `a365 publish` prints `Publish completed successfully`.

---

## Lab 5 — Deploy the code with `a365 deploy` (~10 min)

**You will:** zip your Python code and push it to the Azure Web App created in Lab 3.

### Step 5.1 — Run deploy

```powershell
a365 deploy
```

⏰ **3–5 minutes.** Watch for `Deployment completed successfully`.

**What just happened?** The CLI:
1. Packaged your project (`app.py`, `requirements.txt`, `.env` keys → App Settings).
2. Zip-deployed it to the Web App from Lab 3.
3. Restarted the Web App so it picks up the new code.

### Step 5.2 — Sanity-check the health endpoint

Open in a browser:

```text
https://<webAppUrl>/healthz
```

(Use the `webAppUrl` from `a365.generated.config.json`.)

You should see `{"ok": true}`.

**What just happened?** If `/healthz` returns 200 OK, the Web App is running your Python code. If you get 500 or "site not found", check the Azure portal → your Web App → **Log stream**.

### ✅ Checkpoint 5

`https://<webAppUrl>/healthz` returns `{"ok": true}` in a browser.

---

## Lab 6 — Wire the Teams blueprint Notification URL (~10 min)

**You will:** tell Teams *where* to deliver messages for your agent.

### Step 6.1 — Get your Blueprint ID

Open `a365.generated.config.json` and copy the value of `agentBlueprintId`.

### Step 6.2 — Open the Teams Developer Portal

Browse to:

```text
https://dev.teams.microsoft.com/tools/agent-blueprint/<paste-blueprint-id>/configuration
```

If you see **Access Denied**, your tenant admin must add you to the Teams Developer Portal users.

**What just happened?** The Teams Developer Portal is where you configure how Teams talks to your agent. Without this step the agent is live in Azure but Teams has no idea where to send messages.

### Step 6.3 — Set the Notification URL

- **Agent Type** → `API Based`
- **Notification URL** → the `messagingEndpoint` from `a365.generated.config.json` (looks like `https://<webAppUrl>/api/messages`)
- Click **Save**.

**What just happened?** You wired Teams → Web App. From now on, when a user chats with your agent in Teams, Teams POSTs the message to your Web App's `/api/messages`.

### ✅ Checkpoint 6

In the Teams Developer Portal, your **Notification URL** is saved.

---

## Lab 7 — Request + approve a Teams instance, first chat (~25 min)

**You will:** request an instance of your agent in Teams, have an admin approve it, then chat with it.

### Step 7.1 — Request an instance in Teams

1. Open **Microsoft Teams** → **Apps**.
2. Search for the name you set in `manifest.json` (e.g. `My First A365 Agent`).
3. Click it → **Request Instance** (the button might be `Create Instance` or `Add` depending on the preview build).

**What just happened?** A "blueprint" is the template. An "instance" is one approved running copy. You just asked the tenant admin to approve a running copy of your blueprint.

### Step 7.2 — Admin approves the request

A tenant admin opens:

```text
https://admin.cloud.microsoft/#/agents/all/requested
```

Finds your request → clicks **Approve**.

**What just happened?** The admin OK'd the agent for use in this tenant. The system now provisions the actual agent user identity for Teams.

### Step 7.3 — Wait for the agent user to become searchable

⏰ Approval is **asynchronous** — can take a few minutes to a few hours.

### Step 7.4 — Chat

1. In Teams → **New chat**.
2. Type your agent's display name.
3. Pick it from the suggestions.
4. Say `hello`.

You should get `You said: hello` back.

**What just happened?** Teams found the approved instance, posted your message to its `/api/messages` endpoint (Lab 6), your code echoed it back. Full M365 → Azure → Python → response loop confirmed.

### ✅ Checkpoint 7

A `hello` in Teams returns `You said: hello`.

---

## Lab 8 — Add Agent 365 observability (~20 min)

**You will:** wire OpenTelemetry into `app.py` so every chat turn becomes a trace flowing into the Agent 365 Control Panel.

### Step 8.1 — Install the observability package

```powershell
pip install microsoft-opentelemetry
```

Also add it to `requirements.txt` (so re-deploys include it):

```text
microsoft-agents-hosting-aiohttp
microsoft-agents-hosting-core
microsoft-agents-activity
python-dotenv
microsoft-opentelemetry
```

**What just happened?** `microsoft-opentelemetry` is Microsoft's branded OTel wrapper. It has two destinations: standard Azure Monitor *and* the Agent 365 control plane. We enable both.

### Step 8.2 — Add the imports to `app.py`

```python
from microsoft.opentelemetry import use_microsoft_opentelemetry
from microsoft.opentelemetry.a365.core import BaggageBuilder
from microsoft.opentelemetry.a365.hosting.scope_helpers.populate_baggage import populate
from microsoft.opentelemetry.a365.hosting.token_cache_helpers import (
    AgenticTokenCache,
    AgenticTokenStruct,
)
from microsoft.opentelemetry.a365.runtime import get_observability_authentication_scope
```

**What just happened?** These imports give you the four ingredients: turn-on switch (`use_microsoft_opentelemetry`), context labels (`BaggageBuilder` + `populate`), and per-turn token plumbing (`AgenticTokenCache`).

### Step 8.3 — Turn on observability in `main()`

Right after `load_dotenv()`:

```python
use_microsoft_opentelemetry(
    service_name="my-first-a365-agent",
    enable_a365=True,
    a365_token_resolver=AgenticTokenCache().get_cached_token,
)
```

**What just happened?** One function call wires up the entire pipeline. `enable_a365=True` is the magic flag that turns on the Agent 365 destination — without it, traces would only go to App Insights.

### Step 8.4 — Wrap your message handler with the baggage scope

Replace the `echo` handler body with:

```python
@AGENT_APP.activity("message")
async def echo(context: TurnContext, state: TurnState):
    # Register a per-turn token (OBO mode — simplest)
    token_cache = AgenticTokenCache()
    try:
        token_cache.register_observability(
            agent_id=context.activity.recipient.agentic_app_id,
            tenant_id=context.activity.recipient.tenant_id,
            token_generator=AgenticTokenStruct(
                authorization=None,           # OBO: SDK injects the user token
                turn_context=context,
            ),
            observability_scopes=get_observability_authentication_scope(),
        )
    except Exception as e:
        log.warning("A365 observability token registration failed: %s", e)

    builder = BaggageBuilder()
    populate(builder, context)
    with builder.build():
        user_text = context.activity.text or ""
        await context.send_activity(f"You said: {user_text}")
```

**What just happened?** Three things in one handler:
1. **Register a token** so the per-turn trace can be authenticated to the Agent 365 service.
2. **Populate baggage** — the SDK adds `tenantId`, `conversationId`, `userId` etc. as trace attributes.
3. **Wrap the work** in `with builder.build():` so every span emitted inside carries those attributes.

### Step 8.5 — Enable the exporter in `.env`

Add to `.env`:

```dotenv
ENABLE_A365_OBSERVABILITY_EXPORTER=true
```

**What just happened?** The exporter is opt-in. With this false (or missing), traces stay local — useful while debugging.

### Step 8.6 — Re-deploy

```powershell
a365 deploy
```

Then send another message in Teams (e.g. `test 1`) to generate a fresh trace.

**What just happened?** The redeploy pushed both the new code and the new env var. Within ~30 sec, the next message you send will be traced into the Agent 365 Control Panel.

### ✅ Checkpoint 8

- `requirements.txt` includes `microsoft-opentelemetry`.
- `.env` has `ENABLE_A365_OBSERVABILITY_EXPORTER=true`.
- `a365 deploy` succeeded.
- You sent at least one new message in Teams **after** the redeploy.

---

## Lab 9 — Validate in three portals (~25 min)

**You will:** confirm the agent is visible in all the places admins look.

### Step 9.1 — M365 Admin Center → Agents

Browse to:

```text
https://admin.cloud.microsoft/#/agents/all
```

Confirm:

- [ ] Your agent appears with the name from `manifest.json`.
- [ ] Status is **Active**.

**What just happened?** This is the master list of agents in your tenant. If you don't see yours, the publish step (Lab 4) didn't complete.

### Step 9.2 — Agent 365 Control Panel → Telemetry

Open your agent's **Telemetry / Observability** tab.

Confirm:

- [ ] At least one **turn** appears within 1–5 min.
- [ ] Expanding the turn shows attributes: `tenantId`, `conversationId`, `userId`.

**What just happened?** Traces take a moment to flush. Once they appear, you can drill into every span — message in, handler, any downstream LLM/tool calls, response out.

### Step 9.3 — Defender XDR → Advanced Hunting

Open <https://security.microsoft.com> → **Hunting → Advanced hunting**.

> ℹ️ **Prerequisite.** In **Defender portal → Settings → Cloud apps → App connectors**, make sure the **Microsoft 365 activities** checkbox is on. Without it, `CloudAppEvents` is empty for every query. See [Connect Microsoft 365 to Defender for Cloud Apps](https://learn.microsoft.com/defender-cloud-apps/protect-office-365#prerequisites).

Grab your agent's app id from `a365.generated.config.json` (`agentIdentity.appId`), then paste (and edit the GUID):

```kusto
// Source: https://learn.microsoft.com/microsoft-agent-365/developer/direct-open-telemetry-troubleshooting#verifying-ingestion
let agentIdToFind = "<your-agent-app-id-guid>";
CloudAppEvents
| where Timestamp > ago(1d)
| where ActionType in ("InvokeAgent", "InferenceCall",
                       "ExecuteToolBySDK", "ExecuteToolByGateway", "ExecuteToolByMCPServer")
| extend resData       = parse_json(tostring(RawEventData))
| extend AgentId       = tostring(resData.AgentId)
| extend TargetAgentId = tostring(resData.TargetAgentId)
| extend AlternateId   = tostring(resData.PlatformTargetAgentId)
| where AgentId == agentIdToFind
     or TargetAgentId == agentIdToFind
     or AlternateId == agentIdToFind
| project Timestamp, ActionType, AccountDisplayName,
          ConversationId = tostring(resData.ConversationId), resData
| top 50 by Timestamp desc
```

Click **Run query**.

Confirm:

- [ ] Rows appear (within 5–15 min of the first message).

**What just happened?** Agent 365 telemetry flows into Defender XDR's **`CloudAppEvents`** table (there is no separate `AgentActivity` table). Each row is one span — `ActionType` is the operation (`InvokeAgent`, `ExecuteToolBySDK`, …) and the per-span attributes live inside `RawEventData`. Security teams hunt here for unusual agent behaviour.

> 💡 Only runs that emit an `invoke_agent` root span appear in Defender's *agent-activity views* and in the Microsoft 365 admin center. Other operations are still queryable from `CloudAppEvents` but are invisible to those higher-level surfaces.

### Step 9.4 — Write your own KQL

For practice, write a query that counts distinct users in the last 24h:

<details>
<summary>Answer</summary>

```kusto
let agentIdToFind = "<your-agent-app-id-guid>";
CloudAppEvents
| where Timestamp > ago(24h)
| where ActionType == "InvokeAgent"
| extend AgentId = tostring(parse_json(tostring(RawEventData)).AgentId)
| where AgentId == agentIdToFind
| summarize uniqueUsers = dcount(AccountObjectId)
```

> 💧 `CloudAppEvents` has no `UserPrincipalName` column — use `AccountObjectId` (Entra GUID) or `AccountDisplayName` instead.

</details>

### ✅ Checkpoint 9

The agent appears in all 3 portals: Admin Center (Active), Control Panel (1+ traces), Defender XDR (1+ rows).

---

## Lab 10 — Cleanup (~10 min)

**You will:** delete the Azure resources so you stop paying for them.

### Step 10.1 — Cleanup Azure

```powershell
a365 cleanup azure --agent-name <your-initials>-first-agent
```

**What just happened?** This deletes the resource group, web app, and managed identity. Cost stops immediately.

### Step 10.2 — Cleanup the Entra blueprint

```powershell
a365 cleanup blueprint --agent-name <your-initials>-first-agent
```

**What just happened?** This removes the blueprint registration in Entra and the Teams Developer Portal. **It does NOT remove already-approved agent instances** — those are removed by a tenant admin in the M365 admin center.

### Step 10.3 — Verify

- Azure portal → the resource group is gone.
- `a365.generated.config.json` is now stale — delete it locally if you like.

### ✅ Checkpoint 10

Both cleanup commands succeed. No leftover resource group in Azure.

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| `a365: command not found` | The tool's not on PATH yet. | Open a brand-new terminal so PATH updates pick up. |
| `Forbidden / Authorization_RequestDenied` during `setup all` | You lack the required Entra role. | The CLI prints a PowerShell script — hand it to a Global Admin. |
| Browser sign-in keeps looping | Wrong account selected. | Sign out, re-run `az login --allow-no-subscriptions`, pick the **work** account. |
| Teams autocomplete doesn't show your agent | Agent-user creation is async. | Wait — can take minutes to hours after admin approval. |
| Bot in Teams stays silent | The Notification URL in Teams Developer Portal (Lab 6) is wrong/missing. | Re-check `messagingEndpoint` in `a365.generated.config.json` and re-save. |
| `/healthz` returns 500 | The Web App can't start your Python. | Azure portal → Web App → **Log stream** to see the traceback. |
| No traces in Control Panel | (1) `ENABLE_A365_OBSERVABILITY_EXPORTER=true`? (2) Redeployed? (3) `OtelWrite` app role on Agent Identity? | Check all three; the CLI prints the consent script if (3) is missing. |
| Defender XDR `AgentActivity` not found / query fails | There is no `AgentActivity` table — Agent 365 telemetry lands in `CloudAppEvents`. | Use the canonical query in Step 9.3 (filters `CloudAppEvents` by your agent's app id inside `RawEventData`). |
| Defender XDR `CloudAppEvents` empty | First-time ingestion lag, *or* the Microsoft 365 activities connector isn't on. | Wait 5–15 min and retry. Then verify **Defender portal → Settings → Cloud apps → App connectors → Microsoft 365 activities** is enabled. |
| `cleanup` partially fails | One of the resources was already gone. | Re-run — both cleanup commands are idempotent. |

---

## 🎓 Self-check

1. **What's the difference between an agent blueprint and an agent instance?**

   <details><summary>Show answer</summary>
   A **blueprint** is the template registered once in Entra. An **instance** is one approved running copy in a tenant. Many tenants can adopt the same blueprint; each gets its own instance.
   </details>

2. **Why do you do a `--dry-run` before `a365 setup all`?**

   <details><summary>Show answer</summary>
   So you see the planned resource names + region + permission grants *before* anything is created. It's the `terraform plan` of Agent 365.
   </details>

3. **You see traces in App Insights but not in the Agent 365 Control Panel. Why?**

   <details><summary>Show answer</summary>
   The exporter writes to both, but the A365 destination needs three things: (1) `ENABLE_A365_OBSERVABILITY_EXPORTER=true`, (2) the `OtelWrite` app role on the Agent Identity, and (3) the per-turn `register_observability` call in your handler.
   </details>

4. **Why is `--allow-no-subscriptions` useful when running `az login`?**

   <details><summary>Show answer</summary>
   Some Agent 365 paths don't need an Azure subscription. The flag prevents the login from failing if your account isn't linked to one.
   </details>

5. **You move from one developer machine to another. What do you need to bring with you for `a365 deploy` to still work?**

   <details><summary>Show answer</summary>
   The whole project folder — including `a365.generated.config.json` (it has the resource IDs) and `manifest/` (it has the published blueprint ID). Without those, the CLI doesn't know which Web App to push to or which blueprint to refresh.
   </details>

---

## 🚀 Bonus tasks

1. **Combine with Phase 6** — drop the RAG `lookup_policy` tool into the wrapped agent so policy questions work in Teams.
2. **Add a Defender detection rule** — alert when any agent sends >100 messages in 10 minutes.
3. **CI/CD** — wire `a365 deploy` into a GitHub Actions workflow on push to `main`.
4. **Multi-region** — deploy two instances in different Azure regions and front them with **Azure Front Door**.
5. **Cost guardrails** — set an Azure **Budget Alert** on the resource group at $25/month so you don't get surprised.

---

## 🏁 You're done — with the entire curriculum!

Across 12 phases you have:

- Built echo, routing, stateful, card-driven, LLM-powered, RAG-enabled, Teams + SSO agents.
- Wrapped them with the **Agent 365 enterprise layer**: identity, MCP, notifications, observability.
- Containerized, deployed with `azd`, and monitored in App Insights + Defender XDR.

You're now equipped to design, build, ship, and govern enterprise-grade conversational agents on Microsoft 365 and Azure.

Now go build something amazing — and ping us when it ships. 🎉

🔁 Want to refresh? Jump back to [Phase 0 — Setup](../Phase0_Setup/README.md). Want the big picture? [Curriculum home](../README.md).
