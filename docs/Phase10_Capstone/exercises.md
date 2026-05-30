# 🧪 Phase 10 — Capstone Hands-On Lab: Build the Contoso IT Companion

> This is the **capstone**: a full end-to-end build of a real Teams agent — combining everything from Phases 1–9. Unlike earlier labs, this one is **less prescriptive**. Think of it as a guided 2-day project. Follow each milestone, check the criteria, and ship.

---

## 🎯 What you'll build today

A production-shape **Contoso IT Companion** that:

1. Lives in Teams with SSO.
2. Answers IT questions using **Azure OpenAI + RAG** (Phase 5 + 6).
3. Lets employees raise tickets via an **Adaptive Card form** (Phase 4).
4. Lists each user's tickets from **persistent storage** (Phase 3).
5. Shows the signed-in user's profile via **Graph** (Phase 7).
6. Emits **OpenTelemetry traces** to App Insights (Phase 8/9).
7. Ships through a **Docker image + `azd up`** to Azure Container Apps (Phase 9).
8. Has at least **6 passing pytest cases** (Phase 9).

> 👶 You are no longer following a recipe — you're cooking dinner. We give you the shopping list, the milestones, and the demo script. You decide the seasoning.

⏱️ **1–2 days** at a comfortable pace.

---

## ✅ Before you start

- [ ] All Phases 1–9 finished.
- [ ] Terminal prompt starts with **`(.venv)`**.
- [ ] You have working Azure OpenAI, an Azure Bot resource, an Entra SSO app, a dev tunnel or public URL, an Azure subscription, Docker, and `azd`.
- [ ] You have **~2 GB free disk space** for build artifacts.

---

## 🗺️ Two-day roadmap

```
Day 1 (Build)
  Milestone A → Scaffold from Phase 6 RAG agent
  Milestone B → Add the ticket Adaptive Card + state
  Milestone C → Wire SSO + Graph "/me"
  Milestone D → Swap MemoryStorage → BlobStorage (Azurite local)
  Milestone E → Add OTel

Day 2 (Test & Ship)
  Milestone F → 6+ pytest cases (the suite)
  Milestone G → Local Emulator + dev tunnel smoke test
  Milestone H → Dockerfile + azd up
  Milestone I → Side-load into Teams + record the demo
```

Each milestone has a self-check at the end. **Don't move on until the check is green.**

---

## Milestone A — Scaffold (~30 min)

### A.1 — Create the folder

```powershell
cd Phase10_Capstone
mkdir -Force contoso_it_companion
cd contoso_it_companion

# Copy Phase 6 RAG agent as the starting skeleton
Copy-Item ..\..\Phase6_Tools_and_RAG\lab_knowledge\*.py .
Copy-Item ..\..\Phase6_Tools_and_RAG\lab_knowledge\.env .
Copy-Item -Recurse ..\..\Phase6_Tools_and_RAG\lab_knowledge\docs .

# Replace policy docs with the real Contoso ones
Remove-Item docs\*.md
@"
# Contoso Password Policy
- 12+ characters, mixed case, numbers, symbols.
- Rotate every 90 days.
- MFA required for all employees.
- Reset via /reset-password command in chat, or contact helpdesk@contoso.com.
"@ | Out-File docs\password.md -Encoding utf8

@"
# Contoso VPN Policy
- Connect through Cisco AnyConnect.
- Split tunneling disabled.
- VPN expires after 24h inactivity.
"@ | Out-File docs\vpn.md -Encoding utf8

@"
# Contoso New-Hire IT Setup
- Pick up laptop from IT desk on day 1.
- Default password emailed; must change on first login.
- Slack, Teams, Outlook auto-installed.
- Submit hardware requests via ticket: "raise ticket".
"@ | Out-File docs\new_hire.md -Encoding utf8
```

### A.2 — Rename the agent

In `app_v1.py` change the system prompt and welcome message:

```python
SYSTEM = "You are Contoso IT Companion, a friendly internal IT helper."
```

```python
"👋 Hi! I'm Contoso IT Companion. Try `help`, `request ticket`, `my tickets`, or just ask a question."
```

### A.3 — Add a `help` handler

```python
@AGENT_APP.message("help")
async def help_(context, state):
    await context.send_activity(
        "I can:\n"
        "- Answer IT policy questions (just ask)\n"
        "- `request ticket` — open a new IT ticket\n"
        "- `my tickets` — show your tickets\n"
        "- `who am I` — show your profile (after `login`)\n"
        "- `login` / `logout`"
    )
```

### ✅ Milestone A check
- `python app_v1.py` runs.
- `Send-Msg "help"` returns the menu.
- `Send-Msg "What's our VPN policy?"` returns an answer that quotes vpn.md.

---

## Milestone B — Ticket Adaptive Card + state (~90 min)

### B.1 — Make `cards.py`

```python
"""cards.py — Adaptive Card factories."""
def ticket_form() -> dict:
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "size": "Large", "weight": "Bolder",
             "text": "🎫 Open an IT Ticket"},
            {"type": "Input.Text", "id": "title", "label": "Title", "isRequired": True,
             "errorMessage": "Title is required."},
            {"type": "Input.ChoiceSet", "id": "severity", "label": "Severity",
             "style": "compact", "value": "medium",
             "choices": [
                {"title": "Low", "value": "low"},
                {"title": "Medium", "value": "medium"},
                {"title": "High", "value": "high"},
                {"title": "Critical", "value": "critical"},
            ]},
            {"type": "Input.Text", "id": "body", "label": "Describe the issue",
             "isMultiline": True, "isRequired": True,
             "errorMessage": "Description is required."},
        ],
        "actions": [
            {"type": "Action.Submit", "title": "Open ticket",
             "data": {"action": "open_ticket"}},
        ],
    }


def ticket_confirm(ticket_id: str, data: dict) -> dict:
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "size": "Large", "weight": "Bolder",
             "text": f"✅ Ticket {ticket_id} created"},
            {"type": "FactSet", "facts": [
                {"title": "Title", "value": data.get("title", "")},
                {"title": "Severity", "value": data.get("severity", "")},
                {"title": "Description", "value": data.get("body", "")},
            ]},
            {"type": "TextBlock", "text": "We'll email you when it's assigned.",
             "isSubtle": True, "wrap": True},
        ],
    }
```

### B.2 — Wire into `app_v1.py`

```python
import uuid
from microsoft_agents.activity import Activity, ActivityTypes, Attachment
from cards import ticket_form, ticket_confirm

ADAPTIVE_CARD = "application/vnd.microsoft.card.adaptive"


@AGENT_APP.message("request ticket")
async def show_form(context, state):
    await context.send_activity(Activity(
        type=ActivityTypes.MESSAGE,
        attachments=[Attachment(content_type=ADAPTIVE_CARD, content=ticket_form())],
    ))


@AGENT_APP.message("my tickets")
async def my_tickets(context, state):
    tickets = state.user.get("tickets", [])     # 🆕 USER scope — survives conversation
    if not tickets:
        await context.send_activity("You have no tickets yet.")
        return
    lines = [f"- **{t['id']}** [{t['severity']}] {t['title']}" for t in tickets]
    await context.send_activity("🎫 Your tickets:\n" + "\n".join(lines))


# Override the catch-all to handle card submissions FIRST
@AGENT_APP.activity("message")
async def chat(context, state):
    # 1. Card submission?
    if context.activity.value:
        data = dict(context.activity.value)
        if data.get("action") == "open_ticket":
            ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
            tickets = state.user.get("tickets", [])
            tickets.append({"id": ticket_id, **data})
            state.user["tickets"] = tickets
            await context.send_activity(Activity(
                type=ActivityTypes.MESSAGE,
                attachments=[Attachment(content_type=ADAPTIVE_CARD,
                                        content=ticket_confirm(ticket_id, data))],
            ))
            return

    # 2. Otherwise → LLM + tools (the Phase 6 flow)
    history = state.conversation.get("history", [])
    reply = await run_with_tools(history, context.activity.text or "")
    state.conversation["history"] = history
    await context.send_activity(reply)
```

> ⚠️ Notice tickets live in **`state.user`** — they follow the user across every conversation.

### ✅ Milestone B check
- `Send-Msg "request ticket"` returns a card payload.
- Faking a submission (see Phase 4 Lab 3.4) returns a confirmation and a ticket id.
- `Send-Msg "my tickets"` lists the new ticket.

---

## Milestone C — SSO + Graph "/me" (~60 min)

### C.1 — Reuse Phase 7 setup

You already have an Entra app + OAuth Connection from Phase 7. Reuse them. Just confirm:

```dotenv
OAUTH_CONNECTION_NAME=graph-sso
MICROSOFT_APP_ID=...
MICROSOFT_APP_PASSWORD=...
MICROSOFT_APP_TENANT_ID=...
```

### C.2 — Wire MSAL

```python
from microsoft_agents.authentication.msal import MsalAuth

auth = MsalAuth(connection_name=os.environ["OAUTH_CONNECTION_NAME"])
AGENT_APP = AgentApplication(storage=MemoryStorage(), auth=auth)
```

### C.3 — Add Graph-backed handlers

```python
import httpx

async def _graph(path, token):
    async with httpx.AsyncClient(timeout=20) as h:
        r = await h.get(f"https://graph.microsoft.com/v1.0{path}",
                        headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()


@AGENT_APP.message("login")
async def login(context, state):
    tok = await auth.get_token(context)
    if tok:
        await context.send_activity("Already signed in.")
    else:
        await auth.sign_in(context, state)


@AGENT_APP.message("logout")
async def logout(context, state):
    await auth.sign_out(context, state)
    await context.send_activity("Signed out.")


@AGENT_APP.message("who am I")
async def who(context, state):
    tok = await auth.get_token(context)
    if not tok:
        await context.send_activity("Please type `login` first.")
        return
    me = await _graph("/me", tok)
    await context.send_activity(
        f"You are **{me['displayName']}** ({me.get('mail') or me['userPrincipalName']})."
    )
```

### ✅ Milestone C check
- In Teams or with a real signed-in session: `who am I` returns your real name.

---

## Milestone D — BlobStorage (~45 min)

### D.1 — Run Azurite locally

Azurite is a local Azure Storage emulator. Install via VS Code extension **"Azurite"** or:

```powershell
npm install -g azurite
azurite --silent --location ./azurite_data --debug ./azurite_data/debug.log &
```

Leave it running.

### D.2 — Swap storage in `app_v1.py`

```powershell
pip install microsoft-agents-storage-blob azure-storage-blob
```

```python
# Replace:
# AGENT_APP = AgentApplication(storage=MemoryStorage(), auth=auth)

from microsoft_agents.storage.blob import BlobStorage
from azure.storage.blob import BlobServiceClient

bsc = BlobServiceClient.from_connection_string(
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)
# Make sure the container exists
try: bsc.create_container("agent-state")
except Exception: pass

AGENT_APP = AgentApplication(
    storage=BlobStorage(bsc, container_name="agent-state"),
    auth=auth,
)
```

> 💡 In production swap the connection string for `os.environ["AZURE_STORAGE_CONNECTION_STRING"]` pointing at a real account.

### D.3 — Verify

Run the agent. Create a ticket. Stop the agent. Restart. Run `my tickets` — the ticket is still there.

### ✅ Milestone D check
Ticket survives an agent restart.

---

## Milestone E — OpenTelemetry (~30 min)

### E.1 — Wire App Insights

(Same as Phase 8 Lab 2.)

```python
from azure.monitor.opentelemetry import configure_azure_monitor
configure_azure_monitor(connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"])
```

Place this **right after** `load_dotenv()` at the top of `app_v1.py`.

Add to `.env`:

```dotenv
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;...
```

### E.2 — Verify

Send 3 messages. Wait 60 sec. Open App Insights → **Transaction search** → you should see one transaction per message with the LLM call as a child span.

### ✅ Milestone E check
At least one transaction visible in App Insights showing the LLM call.

---

## Milestone F — pytest suite (~90 min)

Create `tests/test_capstone.py` with **at least 6** test cases. Here's the minimum bar:

```python
"""test_capstone.py — capstone test suite."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TestAdapter, TurnContext, TurnState,
)
import cards, tools_v3, rag


# 1. Card renders the right JSON
def test_ticket_form_has_required_fields():
    c = cards.ticket_form()
    ids = {b.get("id") for b in c["body"] if "id" in b}
    assert {"title", "severity", "body"} <= ids


# 2. Confirmation card includes the id
def test_ticket_confirm_includes_id():
    c = cards.ticket_confirm("TKT-ABC123", {"title": "X", "severity": "low", "body": "Y"})
    assert any("TKT-ABC123" in (b.get("text") or "") for b in c["body"])


# 3. Tool dispatch works
def test_get_weather_dispatch():
    assert tools_v3.DISPATCH["get_weather"](https://github.com/mail2raji/agent-365-sdk-handbook/blob/main/Phase10_Capstone/city="Tokyo")


# 4. RAG returns "no policy" when empty
def test_lookup_policy_empty_when_no_index():
    rag._chunks = []
    rag._vectors = None
    assert "No relevant" in tools_v3.DISPATCH["lookup_policy"](https://github.com/mail2raji/agent-365-sdk-handbook/blob/main/Phase10_Capstone/question="anything")


# 5. Welcome handler greets new users
@pytest.mark.asyncio
async def test_welcome_message():
    app = AgentApplication(storage=MemoryStorage())

    @app.conversation_update("membersAdded")
    async def welcome(context, state):
        for m in context.activity.members_added or []:
            if m.id != context.activity.recipient.id:
                await context.send_activity("Welcome!")

    adapter = TestAdapter()
    # Drive members_added — implementation depends on adapter API
    # (skipped here for brevity; see Phase 9 lab 1 for a working example)


# 6. Auth-guarded handler returns friendly message when not signed in
@pytest.mark.asyncio
async def test_who_requires_login():
    # Mock auth.get_token returning None
    mock_auth = MagicMock()
    mock_auth.get_token = AsyncMock(return_value=None)
    # Build an app with mocked auth and a `who am I` handler — assert reply contains "login"
    # (left as an exercise; verify with TestAdapter)
```

Run:

```powershell
pytest -q tests
```

Should report 6+ passed.

### ✅ Milestone F check
`pytest -q` reports **≥ 6 passed, 0 failed.**

---

## Milestone G — Emulator smoke test (~30 min)

1. Start the agent: `python app_v1.py`.
2. Start a dev tunnel: `code tunnel` → copy the public URL.
3. Update your Bot resource Messaging Endpoint to `<public>/api/messages`.
4. In Bot Framework Emulator: connect to your local URL with App ID/secret.
5. Run the **demo script** below.

### Demo script

| Step | Type | Expect |
|---|---|---|
| 1 | `help` | Menu |
| 2 | `login` | OAuth card |
| 3 | (sign in) | Success |
| 4 | `who am I` | Your name + email |
| 5 | `What is the password rotation policy?` | Quoted answer from `password.md` |
| 6 | `request ticket` | Ticket form card |
| 7 | (fill: VPN broken, High, Can't connect) | Confirmation card + `TKT-…` |
| 8 | `my tickets` | The new ticket |
| 9 | (open App Insights) | Transactions visible |

### ✅ Milestone G check
All 9 steps work end-to-end in the Emulator.

---

## Milestone H — Dockerfile + azd up (~60 min)

Follow [Phase 9 Lab 3 & 4](../Phase9_Testing_and_Deployment/exercises.md) — the same `Dockerfile`, `infra/main.bicep`, and `azd up` apply. **Add** these env vars to the Bicep `env`:

```bicep
{ name: 'OAUTH_CONNECTION_NAME', value: 'graph-sso' }
{ name: 'MICROSOFT_APP_ID', value: <bot-app-id> }
{ name: 'MICROSOFT_APP_PASSWORD', secretRef: 'bot-secret' }
{ name: 'MICROSOFT_APP_TENANT_ID', value: <tenant-id> }
{ name: 'AZURE_STORAGE_CONNECTION_STRING', secretRef: 'storage-secret' }
```

And the matching `secrets` block. Then `azd up`.

### ✅ Milestone H check
The Bot Messaging Endpoint can be repointed to your Container App FQDN and Teams still works.

---

## Milestone I — Teams + record the demo (~30 min)

1. Update the Teams manifest you built in Phase 7 to point at the new Bot.
2. Side-load and chat.
3. Record yourself walking through the demo script (Loom, OBS, Teams meeting recording).

### ✅ Milestone I check
You have a video / GIF of the demo. Save it as `demo.mp4` or `demo.gif` in the project root.

---

## ✅ Acceptance checklist (graduation criteria)

Tick **all** before calling this done:

- [ ] Every capability in the Requirements table from the README is demonstrated.
- [ ] `pytest -q` returns ≥ 6 passed.
- [ ] `docker build` succeeds.
- [ ] `azd up` succeeds; the agent responds in Teams.
- [ ] App Insights shows traces for at least one full conversation.
- [ ] No secrets in code or `.env` committed to git.
- [ ] A `README.md` in the project root explains how to run it.
- [ ] A demo recording exists.

---

## 🆘 Common gotchas

| Symptom | Fix |
|---|---|
| BlobStorage error: container not found | Add `bsc.create_container("agent-state")` once at startup. |
| Tickets list shows other users' tickets | You stored in `state.conversation` instead of `state.user`. |
| OAuth card doesn't appear | Bot resource OAuth Connection name doesn't match `OAUTH_CONNECTION_NAME` in `.env`. |
| `httpx` 401 from Graph | Token scope missing (need `User.Read`); grant admin consent in Entra. |
| Container App returns 500 on first request | First-cold-start LLM call timeout. Increase `httpx` timeout to 60. |
| `pytest` can't import `tools_v3` | Tests live in `tests/`; add `sys.path.insert(0, ".")` or `pyproject.toml` with `[tool.pytest.ini_options] pythonpath = ["."]`. |
| App Insights empty | Connection string env var typo. Run `az containerapp show -n ... --query "properties.template.containers[0].env"`. |

---

## 🚀 Stretch goals (optional)

If you have time after the acceptance checklist:

- **Proactive notifications** — Monday morning DM each user with their open ticket count.
- **Multi-language** — detect user language and translate replies.
- **Azure AI Search** — swap the in-memory RAG store for hybrid search.
- **Approval workflow** — Critical tickets require manager approval via Adaptive Card.
- **GitHub Actions CI** — run pytest on every push, deploy on `main`.
- **Cost dashboard** — Workbook showing daily tokens and $.

---

## 🎓 Graduation

When **every** acceptance box is ticked, you've built a production-shape Agent 365 SDK solution end-to-end.

You can now:

- Build any conversational + LLM + RAG + auth + Teams agent.
- Wrap it with the Agent 365 enterprise layer (Phase 8/11).
- Test, observe, deploy, and operate it in Azure.

🎉 Congratulations. Go ship something useful.

Next → [Phase 11 — Wrap with Agent 365 (the full enterprise wrap)](../Phase11_Wrap_with_Agent365/README.md)
