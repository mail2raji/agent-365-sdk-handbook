# 🧪 Phase 8 — Hands-On Lab: Wrap Your Agent in the Agent 365 Enterprise Layer

> A step-by-step lab. By the end your agent will (a) own a verifiable **Agent 365 identity**, (b) emit **OpenTelemetry traces** you can read, and (c) call a **governed MCP tool**.

> ⚠️ The **Microsoft Agent 365 SDK** is currently **preview / pre-release**. APIs may change. Install commands below use `--prerelease=allow` (uv) or `--pre` (pip). If a command fails for a recent SDK build, the fallback is shown in **🆘 If something goes wrong**.

---

## 🎯 What you'll build today

You'll take the **Phase 6 IT Knowledge Agent** and add the four A365 capabilities one at a time:

1. **OpenTelemetry observability** — every handler, every LLM call, every tool call becomes a span.
2. **Agent 365 identity** — the agent has a cryptographically provable identity (not just a client secret).
3. **Governed MCP toolset** — instead of hard-coding a tool URL, the agent discovers tools from the admin-approved catalog.
4. **A365 Notifications** — send a governed Adaptive Card through the notifications API.

> 👶 Phase 7 made the bot talk to Teams. Phase 8 makes it **enterprise-ready** — audited, traced, governed. Think of A365 as the bot wearing a corporate badge.

⏱️ **About 150 minutes** (most of it install/setup, less actual code).

---

## ✅ Before you start

- [ ] Phase 7 finished — bot works in Teams with SSO.
- [ ] Terminal prompt starts with **`(.venv)`**.
- [ ] You have **uv** installed (`pip install uv`).
- [ ] You have an **Azure subscription** with permission to create:
  - Application Insights resource (for Lab 2)
  - Key Vault (optional but recommended for Lab 3)

> 🚧 **Heads up:** A365 packages depend on tenant-level config that an admin may need to enable (Agent 365 onboarding, MCP catalog approval). If your tenant doesn't have it yet, you can still do Lab 2 (observability) and the *theory* of Labs 3–5. Mark blocked steps as "❗ admin needed" and skip with a clear conscience.

---

## 🗺️ Today's roadmap

```
Lab 1 → Install A365 packages (uv)
Lab 2 → Wire OpenTelemetry into the Knowledge Agent → see traces in App Insights
Lab 3 → Provision an Agent 365 identity (CLI)
Lab 4 → Replace hard-coded tools with a governed MCP toolset
Lab 5 → Send your first governed notification
```

---

## Lab 1 — Install A365 packages (~15 min)

**You will:** install the Agent 365 preview packages and confirm the `a365` CLI works.

### Step 1.1 — Confirm uv

```powershell
pip install --upgrade uv
uv --version
```

You should see `uv 0.x.x`.

### Step 1.2 — Install the A365 packages into your venv

Activate your venv first (prompt starts with `(.venv)`), then:

```powershell
uv pip install --prerelease=allow `
    microsoft-agents-a365-identity `
    microsoft-agents-a365-mcp `
    microsoft-agents-a365-notifications `
    microsoft-agents-a365-observability-otlp `
    microsoft-agents-a365-cli
```

> 💡 If any one package fails ("not found"), it may still be unreleased. Skip it; the rest will install.

### Step 1.3 — Verify

```powershell
pip list | findstr microsoft-agents-a365
```

You should see at least 1–5 lines starting with `microsoft-agents-a365-…`.

```powershell
a365 --help
```

Should print the CLI help.

**What just happened?** You added the Agent 365 "enterprise wrap" packages to your venv. From now on, your agent can use identity, MCP, notifications, and observability — each is just `pip install + import`.

### ✅ Checkpoint 1
At least one A365 package is installed and `a365 --help` runs.

---

## Lab 2 — OpenTelemetry traces (~30 min)

**You will:** wire OTel into the Phase 6 Knowledge Agent and see traces in Application Insights.

### Step 2.1 — Create an Application Insights resource

Azure portal → search **"Application Insights"** → **+ Create**:

| Field | Value |
|---|---|
| Resource group | `rg-agent-labs` (or any) |
| Name | `ai-agent-lab` |
| Region | Pick one near you |
| Workspace mode | Workspace-based |

Click **Review + create → Create**. Wait ~30 sec.

Open the new resource → **Overview** → copy the **Connection String** (looks like `InstrumentationKey=...;IngestionEndpoint=https://…/`).

### Step 2.2 — Make a lab folder from the Phase 6 agent

```powershell
cd Phase8_Agent365_Enterprise
mkdir -Force lab_obs
cd lab_obs

# Copy the Phase 6 RAG agent + tools
Copy-Item ..\..\Phase6_Tools_and_RAG\lab_knowledge\*.py .
Copy-Item ..\..\Phase6_Tools_and_RAG\lab_knowledge\.env .
Copy-Item -Recurse ..\..\Phase6_Tools_and_RAG\lab_knowledge\docs .
```

### Step 2.3 — Add the OTel connection string to `.env`

Open `.env` and append:

```dotenv
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=https://...
OTEL_SERVICE_NAME=knowledge-agent-lab
```

### Step 2.4 — Wire OTel in `app_v1.py`

At the **very top** of `app_v1.py` (before any other import), add:

```python
"""app_v1.py — Knowledge Agent with OTel."""
import os
from dotenv import load_dotenv
load_dotenv()

# Pick whichever of these is available in your A365 install:
try:
    from microsoft_agents_a365.observability.otlp import configure_otel
    configure_otel(
        service_name=os.environ.get("OTEL_SERVICE_NAME", "agent-365-lab"),
    )
except ImportError:
    # Fallback if the A365 OTel package isn't out yet — use the official Azure Monitor exporter
    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(
        connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"],
    )

# … keep the rest of the file unchanged …
```

If `azure-monitor-opentelemetry` is missing:

```powershell
pip install azure-monitor-opentelemetry opentelemetry-instrumentation-httpx
```

### Step 2.5 — Run and generate traffic

```powershell
python app_v1.py
```

In terminal 2:

```powershell
Send-Msg "What's the weather in Tokyo?"
Send-Msg "What is our password rotation policy?"
Send-Msg "Reset my password for alice@contoso.com"
```

### Step 2.6 — Read traces in App Insights

Wait ~60 seconds (telemetry pipeline is slow on first send). Then in the portal → your App Insights resource → **Transaction search** → click any item.

You should see spans like:

- `http POST /api/messages`
- `agent.turn` (or similar)
- `openai.chat.completions.create`
- `httpx GET …` (if RAG embedded)

Also try → **Application map**: a visual graph of agent → OpenAI → external HTTP.

**What just happened?** With **one import** + **one function call**, every HTTP request and OpenAI call your agent makes is now visible in Azure dashboards. No print statements, no manual logging. This is the foundation of operating an agent in production.

### ✅ Checkpoint 2
Three messages = three traces, each showing the LLM call as a child span.

Stop the agent.

---

## Lab 3 — Provision an Agent 365 identity (~20 min)

**You will:** create a real **agent identity** (not a Bot secret) so the agent acts as itself, with scoped permissions, like any other enterprise app.

> ❗ Tenant admin permissions required to create A365 identities. If you don't have them, **read through** and skip the actual command — the rest of the labs still work without an A365 identity (the SDK falls back to the Phase 7 Bot identity).

### Step 3.1 — Log in

```powershell
a365 login
```

It opens a browser. Sign in with your tenant admin account.

### Step 3.2 — Create the identity

```powershell
a365 identity create `
    --display-name "Knowledge Agent Lab" `
    --owner "your.email@yourtenant.onmicrosoft.com" `
    --scopes "tickets.read,policy.read" `
    --output ./identity
```

This creates `./identity/agent.pem` (private key) and prints an identity client id. Add to `.env`:

```dotenv
A365_IDENTITY_CLIENT_ID=<printed-id>
A365_IDENTITY_TENANT_ID=<your tenant id>
A365_IDENTITY_KEY_PATH=./identity/agent.pem
```

### Step 3.3 — Use the identity in code

In `app_v1.py`, replace the `AGENT_APP = …` line:

```python
from microsoft_agents_a365.identity import AgentIdentity

identity = AgentIdentity.from_env()    # reads the 3 vars above
AGENT_APP = AgentApplication(storage=MemoryStorage(), identity=identity)
```

### Step 3.4 — Restart & verify

```powershell
python app_v1.py
```

In the App Insights logs (`union traces, dependencies | where timestamp > ago(5m)`) you should see the identity client id attached as an attribute on each span.

**What just happened?** The agent now has its **own** identity — not a shared Bot secret. In an audit you can say "this trace was the Knowledge Agent, scope: tickets.read, owner: alice". That's the difference between a hobby bot and an enterprise agent.

### ✅ Checkpoint 3
`a365 identity list` shows your new identity, and spans show `agent.identity` attribute.

---

## Lab 4 — Governed MCP toolset (~30 min)

**You will:** swap the hard-coded TOOL_SCHEMAS list with a list discovered from the governed MCP catalog.

### Step 4.1 — Register a tool manifest

Create `mcp_ticket_lookup.yaml`:

```yaml
name: ticket-lookup
description: Look up an IT support ticket by ID.
endpoint: https://mcp.contoso.com/ticket-lookup    # mock endpoint
schema:
  type: object
  properties:
    ticket_id: { type: string }
  required: [ticket_id]
scopes: [tickets.read]
```

Register:

```powershell
a365 mcp register --manifest mcp_ticket_lookup.yaml
```

> ⚠️ The tool now sits in the catalog as **pending admin approval**. An admin must approve it in the Agent 365 portal. If you don't have admin rights, you can still continue with the *existing* approved tools in your tenant — `a365 mcp list` shows what's available.

### Step 4.2 — Make `mcp_tools.py`

```powershell
New-Item mcp_tools.py -ItemType File
code mcp_tools.py
```

Paste:

```python
"""mcp_tools.py — discover governed tools from the A365 catalog."""
import asyncio
from microsoft_agents_a365.mcp import McpToolset


async def load_governed_tools(identity):
    toolset = await McpToolset.from_catalog(identity)
    schemas = toolset.openai_tools()    # the same shape the LLM expects
    print(f"[MCP] discovered {len(schemas)} governed tool(s):")
    for s in schemas:
        print(f"  - {s['function']['name']}")
    return toolset, schemas
```

### Step 4.3 — Wire it into the agent

In `app_v1.py`, **after** identity is created, **before** `start_server`:

```python
from mcp_tools import load_governed_tools

# Discover the catalog at startup
_mcp_toolset, GOVERNED_SCHEMAS = asyncio.run(load_governed_tools(identity))

# Merge with your local tools — locals first so they win on name conflicts
ALL_SCHEMAS = TOOL_SCHEMAS + GOVERNED_SCHEMAS

async def dispatch_tool(name, args):
    if name in DISPATCH:
        return DISPATCH[name](https://github.com/mail2raji/agent-365-sdk-handbook/blob/main/Phase8_Agent365_Enterprise/**args)
    return await _mcp_toolset.invoke(name, args)
```

Then in `run_with_tools`, replace the `result = DISPATCH[name](https://github.com/mail2raji/agent-365-sdk-handbook/blob/main/Phase8_Agent365_Enterprise/**args)` line with:

```python
result = await dispatch_tool(name, args)
```

And in the API call, pass `tools=ALL_SCHEMAS` instead of `TOOL_SCHEMAS`.

### Step 4.4 — Run & test

```powershell
python app_v1.py
```

```powershell
Send-Msg "Look up ticket TKT-1234"
```

If the MCP server is reachable and approved, you'll see:

```text
[TOOL CALL] ticket-lookup({'ticket_id': 'TKT-1234'})
```

And the LLM weaves the answer into the reply.

**What just happened?** Your tools are no longer hard-coded in Python — they live in a **central catalog** an admin curates. Add a new approved tool, and every wrapped agent picks it up at next start. This is how you scale to dozens of agents without copy-paste.

### ✅ Checkpoint 4
The agent discovers governed tools at startup and the LLM uses them alongside local tools.

---

## Lab 5 — Send a governed notification (~15 min)

**You will:** send a notification to yourself (or a test user) using the A365 Notifications API.

### Step 5.1 — Register a template

Create `weekly_summary.json` (an Adaptive Card template):

```json
{
  "type": "AdaptiveCard",
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "version": "1.5",
  "body": [
    { "type": "TextBlock", "size": "Large", "weight": "Bolder",
      "text": "🗓 Weekly IT Summary" },
    { "type": "FactSet", "facts": [
        { "title": "Open tickets", "value": "{tickets_open}" },
        { "title": "Avg resolution (h)", "value": "{avg_resolution_hours}" }
      ]
    }
  ]
}
```

Register it:

```powershell
a365 notifications template register `
    --id weekly-summary-v1 `
    --card weekly_summary.json
```

### Step 5.2 — Send one notification

Create `send_test_notification.py`:

```python
"""send_test_notification.py — send one A365 notification."""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from microsoft_agents_a365.identity import AgentIdentity
from microsoft_agents_a365.notifications import NotificationClient, Notification

async def main():
    identity = AgentIdentity.from_env()
    notifier = NotificationClient(identity)
    await notifier.send(Notification(
        template_id="weekly-summary-v1",
        audience={"user_upn": "your.email@yourtenant.onmicrosoft.com"},
        data={"tickets_open": 3, "avg_resolution_hours": 18.5},
    ))
    print("Notification sent.")

asyncio.run(main())
```

Run:

```powershell
python send_test_notification.py
```

Check your **Teams Activity feed** or **chat with the agent** — the card should arrive.

**What just happened?** A **proactive** notification = the agent talks **first**, instead of waiting for the user. Combined with templates (registered & approved by admin) you get a governed channel for things like daily summaries, alerts, or reminders.

### ✅ Checkpoint 5
The notification card appears in Teams for the target user.

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| `pip install … no matching distribution` | The A365 package isn't published to the registry your pip sees. | Use `uv pip install --prerelease=allow`. If still missing, the package may not be released yet — wait or use the **Azure Monitor** fallback shown in Lab 2. |
| `a365 login` opens browser then fails | Wrong tenant or A365 not onboarded. | Ask your admin to onboard the tenant to A365 (preview). |
| `Permission denied: ./identity/agent.pem` | Wrong file mode. | `icacls .\identity\agent.pem /inheritance:r /grant:r "$($env:USERNAME):F"` (Windows). |
| Traces show in console but not in App Insights | Connection string missing or wrong. | Re-copy from the portal; restart agent. |
| `McpToolset.from_catalog` returns 0 tools | No tools approved in your tenant yet. | Ask admin to approve at least one via Agent 365 portal. |
| Notification doesn't arrive | Template not approved, or wrong audience UPN. | `a365 notifications template list` to verify status; double-check the email. |
| `KeyError: A365_IDENTITY_CLIENT_ID` | `.env` not loaded before identity. | Move `load_dotenv()` to line 1 of `app_v1.py`. |

---

## 🎓 Self-check

1. **What's the difference between Microsoft 365 Agents SDK and Microsoft Agent 365 SDK?**

   <details><summary>Show answer</summary>
   The **365 Agents SDK** (Phases 1–7) is the foundation — handlers, state, channels. The **Agent 365 SDK** (Phase 8) is the *enterprise layer* — identity, observability, governed MCP, notifications. A365 builds on the foundation, not the other way around.
   </details>

2. **Why use Agent 365 identity instead of a Bot App Registration?**

   <details><summary>Show answer</summary>
   A365 identity is cryptographically verifiable, tied to admin policy, and auditable in Purview. A Bot App Reg is just a client secret — anyone with the secret can impersonate the bot.
   </details>

3. **What does `configure_otel(...)` instrument automatically?**

   <details><summary>Show answer</summary>
   Every SDK handler invocation (spans), `httpx` requests, OpenAI calls, and governed MCP calls. You don't need to add `tracer.start_as_current_span(...)` manually for those.
   </details>

4. **In governed MCP, who decides which tools your agent can call?**

   <details><summary>Show answer</summary>
   The tenant admin via the Agent 365 portal. The agent merely *discovers* what's been approved — it can't bypass the catalog.
   </details>

5. **Where does a governed notification end up if Teams isn't available?**

   <details><summary>Show answer</summary>
   The Notifications service routes to whatever channels the audience is configured for — email, Teams, M365 Copilot, etc. Routing is centralized, not per-agent.
   </details>

---

## 🚀 Bonus tasks

1. **Custom span attribute** — add `trace.get_current_span().set_attribute("user.role", "manager")` in a handler and see it in App Insights logs.
2. **Two identities, one agent** — provision a second A365 identity (`dev-knowledge-agent`) and switch via env var.
3. **Notification on tool failure** — wrap `dispatch_tool` in try/except and send a notification to admins when a tool errors.
4. **MCP unit test** — mock `McpToolset.from_catalog` to return 2 fake tools; verify the agent merges them with locals.
5. **OTel local exporter** — install `opentelemetry-exporter-console` and route traces to your terminal instead of App Insights for fast local iteration.

---

## 🏁 You're done!

You can now:

- Install and recognise A365 vs base SDK packages.
- Wire OpenTelemetry and read traces in App Insights.
- Provision and use an Agent 365 identity.
- Discover governed MCP tools from the catalog.
- Send A365 notifications from templates.

Next → [Phase 9 — Testing, Debugging & Deployment](../Phase9_Testing_and_Deployment/README.md)
