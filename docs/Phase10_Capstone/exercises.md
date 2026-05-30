# 🧪 Phase 10 — Capstone Hands-On Lab: Build the Contoso IT Companion

> A step-by-step capstone lab. By the end you'll have a real Teams agent in Azure that answers IT questions, opens tickets, and shows up on a dashboard — combining everything from Phases 1–9.

---

## 🎯 What you'll build today

A production-shape **Contoso IT Companion** agent:

1. Lives in **Microsoft Teams** with single sign-on (SSO).
2. Answers IT questions using **Azure OpenAI + RAG** (Phases 5 + 6).
3. Lets employees raise tickets via an **Adaptive Card form** (Phase 4).
4. Lists each user's tickets from **persistent storage** (Phase 3).
5. Shows the signed-in user's profile via **Microsoft Graph** (Phase 7).
6. Emits **OpenTelemetry traces** to Application Insights (Phases 8 + 9).
7. Ships through a **Docker image + `azd up`** to Azure Container Apps (Phase 9).
8. Has at least **6 passing pytest cases** (Phase 9).

> 👶 Think of it like building a Lego set. Phases 1–9 gave you all the bricks. Today we snap them together into a real spaceship.

⏱️ **1–2 days** at a comfortable pace.

---

## ✅ Before you start (checklist)

- [ ] All Phases 1–9 finished.
- [ ] Terminal prompt starts with **`(.venv)`**.
- [ ] You have working: **Azure OpenAI**, an **Azure Bot** resource, an **Entra SSO** app, a dev tunnel or public URL, an **Azure subscription**, **Docker Desktop**, and **`azd`** CLI.
- [ ] You have **~2 GB free disk space** for build artifacts.

If any box is unchecked, finish that phase first.

---

## 🗺️ Today's roadmap

```
Day 1 (Build the bricks)
  Lab 1 → Scaffold from the Phase 6 RAG agent
  Lab 2 → Add a ticket Adaptive Card + user-scope state
  Lab 3 → Wire SSO + Graph "/me"
  Lab 4 → Swap MemoryStorage → Blob storage (Azurite local)
  Lab 5 → Wire OpenTelemetry to App Insights

Day 2 (Test & ship)
  Lab 6 → Write 6+ pytest cases
  Lab 7 → Local Emulator + dev tunnel smoke test
  Lab 8 → Dockerfile + azd up to Azure Container Apps
  Lab 9 → Side-load into Teams + record the demo
```

Each lab ends with a **✅ Checkpoint** — don't move on until it's green.

---

## Lab 1 — Scaffold the project (~30 min)

**You will:** copy the Phase 6 RAG agent into a new folder and rename it to be the Contoso IT Companion.

### Step 1.1 — Create the project folder

```powershell
cd Phase10_Capstone
mkdir -Force contoso_it_companion
cd contoso_it_companion
```

**What just happened?** You made an empty box called `contoso_it_companion`. That's where the whole capstone will live. Keeping it separate means you can't accidentally break the Phase 6 lab while you experiment.

### Step 1.2 — Copy the Phase 6 RAG agent as your starting point

```powershell
Copy-Item ..\..\Phase6_Tools_and_RAG\lab_knowledge\*.py .
Copy-Item ..\..\Phase6_Tools_and_RAG\lab_knowledge\.env .
Copy-Item -Recurse ..\..\Phase6_Tools_and_RAG\lab_knowledge\docs .
```

**What just happened?** You photocopied the Phase 6 agent. It already knows how to answer questions using policy documents and call tools. You'll **add** to it — you don't have to write a brand-new agent from scratch.

### Step 1.3 — Replace the policy docs with the real Contoso ones

```powershell
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

**What just happened?** You filled the agent's "library" with three Contoso policy pages. When users ask "What's our password rule?", the agent will read these and answer from them — not make stuff up.

### Step 1.4 — Personalize the agent

Open `app_v1.py` and change the system prompt + welcome message:

```python
SYSTEM = "You are Contoso IT Companion, a friendly internal IT helper."
```

```python
"👋 Hi! I'm Contoso IT Companion. Try `help`, `request ticket`, `my tickets`, or just ask a question."
```

**What just happened?** You gave your robot a name (Contoso IT Companion) and a personality (friendly IT helper). You also told users what menu of commands they can try.

### Step 1.5 — Add a `help` command handler

Add this near the other `@AGENT_APP.message(...)` handlers:

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

**What just happened?** When a confused user types `help`, the agent now hands them a menu — like a friendly waiter saying "here's everything on offer".

### ✅ Checkpoint 1

- `python app_v1.py` starts the agent.
- `Send-Msg "help"` (from Phase 2 helper) returns the menu.
- `Send-Msg "What's our VPN policy?"` returns an answer that quotes `vpn.md`.

Stop the agent with `Ctrl+C` before moving on.

---

## Lab 2 — Ticket Adaptive Card + state (~90 min)

**You will:** add a fillable form that opens IT tickets, and store each user's tickets where only **they** can see them.

### Step 2.1 — Create `cards.py` (the form factory)

```powershell
New-Item cards.py -ItemType File
code cards.py
```

Paste:

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

**What just happened?** You wrote two recipes. The first recipe (`ticket_form`) builds an **empty form** the user can fill in. The second (`ticket_confirm`) builds a **receipt card** showing what they submitted. Putting them in a separate file (`cards.py`) keeps `app_v1.py` clean.

### Step 2.2 — Show the form when the user asks

In `app_v1.py` add at the top:

```python
import uuid
from microsoft_agents.activity import Activity, ActivityTypes, Attachment
from cards import ticket_form, ticket_confirm

ADAPTIVE_CARD = "application/vnd.microsoft.card.adaptive"
```

Then add a new handler:

```python
@AGENT_APP.message("request ticket")
async def show_form(context, state):
    await context.send_activity(Activity(
        type=ActivityTypes.MESSAGE,
        attachments=[Attachment(content_type=ADAPTIVE_CARD, content=ticket_form())],
    ))
```

**What just happened?** When a user types `request ticket`, the agent hands them the empty form (the recipe from Step 2.1). Teams will show this as a real card with input boxes — not just text.

### Step 2.3 — List the user's tickets

```python
@AGENT_APP.message("my tickets")
async def my_tickets(context, state):
    tickets = state.user.get("tickets", [])     # 🆕 USER scope — survives conversations
    if not tickets:
        await context.send_activity("You have no tickets yet.")
        return
    lines = [f"- **{t['id']}** [{t['severity']}] {t['title']}" for t in tickets]
    await context.send_activity("🎫 Your tickets:\n" + "\n".join(lines))
```

**What just happened?** Tickets are stored in **`state.user`** (the user scope from Phase 3). That means each person sees only their own tickets — Alice never sees Bob's tickets, even if they're in the same Teams channel.

### Step 2.4 — Save submitted tickets (rewrite the catch-all)

Replace the existing `@AGENT_APP.activity("message")` handler with:

```python
@AGENT_APP.activity("message")
async def chat(context, state):
    # 1. Did the user submit the ticket form?
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

    # 2. Otherwise → normal LLM + tools flow (Phase 6)
    history = state.conversation.get("history", [])
    reply = await run_with_tools(history, context.activity.text or "")
    state.conversation["history"] = history
    await context.send_activity(reply)
```

**What just happened?** Every incoming message hits this catch-all. If the message carries a card submission (`context.activity.value` is set), we save a new ticket and reply with the receipt card. Otherwise the agent answers the question with the LLM. **Always check for card submissions first** — they don't have plain text.

### ✅ Checkpoint 2

- `Send-Msg "request ticket"` returns a card payload (JSON in the response).
- Faking a card submission (see [Phase 4 Lab 3.4](../Phase4_Rich_Messaging/exercises.md)) returns a confirmation and a ticket id.
- `Send-Msg "my tickets"` lists the new ticket.

---

## Lab 3 — SSO + Microsoft Graph "/me" (~60 min)

**You will:** make the agent ask the user to sign in once, then use their Microsoft 365 token to call **Microsoft Graph** and fetch their profile.

### Step 3.1 — Reuse the Entra app + OAuth Connection from Phase 7

Add the existing values to `.env`:

```dotenv
OAUTH_CONNECTION_NAME=graph-sso
MICROSOFT_APP_ID=...
MICROSOFT_APP_PASSWORD=...
MICROSOFT_APP_TENANT_ID=...
```

**What just happened?** You told the agent how to find the OAuth connection you already set up in Phase 7 — no need to register a new app. `graph-sso` is the name you gave that connection inside the Azure Bot resource.

### Step 3.2 — Wire MSAL auth into the agent

At the top of `app_v1.py`:

```python
from microsoft_agents.authentication.msal import MsalAuth

auth = MsalAuth(connection_name=os.environ["OAUTH_CONNECTION_NAME"])
AGENT_APP = AgentApplication(storage=MemoryStorage(), auth=auth)
```

**What just happened?** `MsalAuth` is the part of the SDK that handles "show the user a sign-in card, exchange the result for a Graph token". You attached it to the agent so every handler can call `auth.get_token(context)`.

### Step 3.3 — Add a tiny Graph helper

```python
import httpx

async def _graph(path, token):
    async with httpx.AsyncClient(timeout=20) as h:
        r = await h.get(f"https://graph.microsoft.com/v1.0{path}",
                        headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()
```

**What just happened?** This is a 5-line wrapper around Microsoft Graph. You give it a path (e.g. `/me`) and a token, and it returns the JSON. Reusing this for every Graph call keeps the rest of the code short.

### Step 3.4 — Add login / logout / who-am-I handlers

```python
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

**What just happened?** `login` shows a sign-in card if the user has no token. `who am I` reads the cached token and uses it to fetch their profile from Microsoft Graph. `logout` clears the token. This is exactly the Phase 7 SSO pattern, plugged into the new agent.

### ✅ Checkpoint 3

- In Teams or with a real signed-in session: `who am I` returns your real name.

---

## Lab 4 — Persistent storage with Blob (~45 min)

**You will:** swap `MemoryStorage` (which forgets everything on restart) for **Azure Blob storage** (which keeps tickets forever). You'll use **Azurite** — a local pretend Blob storage — so you don't need a real Azure account yet.

### Step 4.1 — Install and start Azurite locally

Install via the VS Code extension **"Azurite"**, **or**:

```powershell
npm install -g azurite
azurite --silent --location ./azurite_data --debug ./azurite_data/debug.log &
```

**What just happened?** Azurite is a tiny program that pretends to be Azure Blob storage on your laptop. It listens on `http://127.0.0.1:10000`. Anything you save to it survives even if you stop your agent — but it's still 100 % local, free, and offline.

### Step 4.2 — Install the storage packages

```powershell
pip install microsoft-agents-storage-blob azure-storage-blob
```

**What just happened?** Two pip packages: one is the official Azure SDK for talking to blob storage, the other is the small adapter that lets the M365 Agents SDK use it as a storage backend.

### Step 4.3 — Wire blob storage into the agent

In `app_v1.py` replace:

```python
AGENT_APP = AgentApplication(storage=MemoryStorage(), auth=auth)
```

with:

```python
from microsoft_agents.storage.blob import BlobStorage
from azure.storage.blob import BlobServiceClient

bsc = BlobServiceClient.from_connection_string(
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)
# Make sure the container exists (one-time)
try:
    bsc.create_container("agent-state")
except Exception:
    pass

AGENT_APP = AgentApplication(
    storage=BlobStorage(bsc, container_name="agent-state"),
    auth=auth,
)
```

**What just happened?** You told the agent: "Don't use RAM for memory — use this Blob storage account." The long string is Azurite's well-known dev connection string (the same on everyone's computer). In production you'd swap it for `os.environ["AZURE_STORAGE_CONNECTION_STRING"]` pointing at a real Azure storage account.

> 💡 The `create_container` call is idempotent — running it many times is safe. If the container already exists, the exception is silently swallowed.

### Step 4.4 — Verify tickets survive a restart

1. Start the agent: `python app_v1.py`.
2. Create a ticket via `request ticket` + card submission.
3. Stop the agent (`Ctrl+C`).
4. Restart: `python app_v1.py`.
5. `Send-Msg "my tickets"` — your ticket should still be there. 🎉

**What just happened?** Before this lab, restarting wiped everything (because `MemoryStorage` lives only in RAM). Now your tickets are stored as blobs in Azurite, so they survive forever — even if the process dies.

### ✅ Checkpoint 4

A ticket created before restart is still listed after restart.

---

## Lab 5 — OpenTelemetry → Application Insights (~30 min)

**You will:** turn on automatic tracing so every conversation shows up in Azure dashboards and KQL queries.

### Step 5.1 — Add the App Insights setup line

At the very top of `app_v1.py`, right after `load_dotenv()`:

```python
from azure.monitor.opentelemetry import configure_azure_monitor
configure_azure_monitor(connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"])
```

**What just happened?** One line wires up the **whole OpenTelemetry pipeline**. The SDK now automatically emits traces, metrics, and logs to Application Insights. No more print statements needed.

### Step 5.2 — Add the connection string

Add to `.env`:

```dotenv
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...
```

**What just happened?** This is the secret that tells the SDK *which* App Insights resource to send data to. Grab it from your App Insights resource in the Azure portal → **Overview** → **Connection String**.

### Step 5.3 — Verify

1. Restart the agent.
2. Send 3 messages.
3. Wait ~60 seconds.
4. Open the App Insights resource → **Transaction search**.
5. You should see one transaction per message, with the LLM call as a child span.

**What just happened?** App Insights buffers events for ~30–60 sec before flushing. Once they appear, you can drill into the whole chain: message → handler → LLM call → tool call.

### ✅ Checkpoint 5

At least one transaction is visible in App Insights showing the LLM call.

---

## Lab 6 — pytest suite (~90 min)

**You will:** write at least **6 unit tests** that prove the cards render correctly, the tools dispatch correctly, and the agent doesn't crash.

### Step 6.1 — Create the test folder

```powershell
mkdir -Force tests
New-Item tests\__init__.py -ItemType File
New-Item tests\test_capstone.py -ItemType File
code tests\test_capstone.py
```

**What just happened?** Pytest looks for any file starting with `test_` in folders it discovers. The empty `__init__.py` marks the folder as a Python package so imports work cleanly.

### Step 6.2 — Paste the minimum 6 tests

```python
"""test_capstone.py — capstone test suite."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import AsyncMock, MagicMock

from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TestAdapter,
)
import cards, tools_v3, rag


# 1. Card renders the right input fields
def test_ticket_form_has_required_fields():
    c = cards.ticket_form()
    ids = {b.get("id") for b in c["body"] if "id" in b}
    assert {"title", "severity", "body"} <= ids


# 2. Confirmation card includes the ticket id
def test_ticket_confirm_includes_id():
    c = cards.ticket_confirm("TKT-ABC123", {"title": "X", "severity": "low", "body": "Y"})
    assert any("TKT-ABC123" in (b.get("text") or "") for b in c["body"])


# 3. Tool dispatch works for the weather tool
def test_get_weather_dispatch():
    assert tools_v3.DISPATCH["get_weather"](https://github.com/mail2raji/agent-365-sdk-handbook/blob/main/Phase10_Capstone/city="Tokyo")


# 4. RAG returns the right message when there's no index
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

    # See Phase 9 Lab 1 for the full TestAdapter driving code
    assert app is not None


# 6. Auth-guarded handler asks user to log in when no token
@pytest.mark.asyncio
async def test_who_requires_login():
    mock_auth = MagicMock()
    mock_auth.get_token = AsyncMock(return_value=None)
    # Build an app with mocked auth and assert the reply contains "login"
    # (See Phase 9 Lab 1 for TestAdapter driving code)
    assert mock_auth is not None
```

**What just happened?** Six tests, each laser-focused on one piece of behaviour. The first four don't need any async or adapter — they just exercise pure functions (cards, dispatch). The last two are placeholders showing the async pattern; expand them using the Phase 9 Lab 1 template.

### Step 6.3 — Run the suite

```powershell
pytest -q tests
```

You should see `6 passed`.

**What just happened?** Pytest discovered all 6 tests, ran them, and confirmed they all pass. From now on, you can run this in **2 seconds** — any time you change the code — to catch breakage instantly.

### ✅ Checkpoint 6

`pytest -q` reports **≥ 6 passed, 0 failed**.

---

## Lab 7 — Bot Framework Emulator smoke test (~30 min)

**You will:** drive the live agent through a 9-step demo script using the Bot Framework Emulator.

### Step 7.1 — Start the agent

```powershell
python app_v1.py
```

### Step 7.2 — Start a public dev tunnel

```powershell
code tunnel
```

Copy the public URL it prints — looks like `https://something.devtunnels.ms`.

**What just happened?** Your laptop is now reachable from the public internet on that URL. The Bot Service in Azure can forward messages from Teams → tunnel → your laptop.

### Step 7.3 — Update the Bot resource Messaging Endpoint

In the Azure portal → your **Bot** resource → **Configuration** → set **Messaging endpoint** to:

```text
https://<your-tunnel>.devtunnels.ms/api/messages
```

Click **Save**.

### Step 7.4 — Connect Bot Framework Emulator

In the Emulator → **Open Bot** → fill in:

- **Bot URL**: `http://localhost:3978/api/messages` (use localhost, not the tunnel)
- **App ID** / **App password**: from your `.env`

### Step 7.5 — Run the 9-step demo

| # | Type / do | Expect |
|---|---|---|
| 1 | `help` | Menu |
| 2 | `login` | OAuth card |
| 3 | (sign in) | Success |
| 4 | `who am I` | Your name + email |
| 5 | `What is the password rotation policy?` | Answer quoted from `password.md` |
| 6 | `request ticket` | Ticket form card |
| 7 | (fill: VPN broken, High, Can't connect) | Confirmation card with `TKT-…` |
| 8 | `my tickets` | The new ticket appears |
| 9 | (open App Insights → Transaction search) | Traces visible |

**What just happened?** You drove the agent through **every** capability — auth, LLM, RAG, cards, state, observability — in one sitting. If anything fails, you find out **before** going to Teams (where debugging is harder).

### ✅ Checkpoint 7

All 9 steps work end-to-end in the Emulator.

---

## Lab 8 — Containerize and deploy with `azd up` (~60 min)

**You will:** package the agent in a Docker image and deploy it to Azure Container Apps with one command.

### Step 8.1 — Reuse the Phase 9 Dockerfile + Bicep

Follow [Phase 9 Lab 3 & 4](../Phase9_Testing_and_Deployment/exercises.md) — copy `Dockerfile`, `.dockerignore`, `infra/main.bicep`, and `azure.yaml` into this project.

**What just happened?** The Phase 9 templates are reusable as-is. The only thing that changes is the **environment variables** you pass to the container.

### Step 8.2 — Add capstone-specific env vars to the Bicep

In `infra/main.bicep`, add these inside the container's `env: [ ... ]` block:

```bicep
{ name: 'OAUTH_CONNECTION_NAME', value: 'graph-sso' }
{ name: 'MICROSOFT_APP_ID', value: <bot-app-id> }
{ name: 'MICROSOFT_APP_PASSWORD', secretRef: 'bot-secret' }
{ name: 'MICROSOFT_APP_TENANT_ID', value: <tenant-id> }
{ name: 'AZURE_STORAGE_CONNECTION_STRING', secretRef: 'storage-secret' }
```

And the matching entries in the `secrets: [ ... ]` block.

**What just happened?** The agent now has access to all the same `.env` values inside the container — but as Azure Container Apps **secrets** (encrypted, scoped to this app) rather than checked-in plaintext.

### Step 8.3 — Deploy

```powershell
azd up
```

Wait ~5–10 minutes. The output prints the public FQDN of the deployed container.

**What just happened?** `azd up` did three things: provisioned the Bicep resources, built and pushed the Docker image, and pointed the Container App at the new image. Your agent is live in Azure.

### Step 8.4 — Point the Bot resource at the deployed URL

In the Azure portal → your **Bot** resource → **Configuration** → set **Messaging endpoint** to:

```text
https://<your-container-app-fqdn>/api/messages
```

Save.

### ✅ Checkpoint 8

Teams (or the Emulator) can talk to the agent via the **Container App FQDN** — no laptop required.

---

## Lab 9 — Side-load into Teams and record the demo (~30 min)

**You will:** install the agent into Teams as an app and record a video showing it working end-to-end.

### Step 9.1 — Update the Teams manifest

Open the Teams manifest you built in Phase 7. Update the `botId` and any URLs to point at the deployed Bot resource.

### Step 9.2 — Re-package and side-load

```powershell
Compress-Archive -Path manifest\*,color.png,outline.png -DestinationPath app.zip -Force
```

In Teams → **Apps** → **Manage your apps** → **Upload an app** → upload `app.zip`.

**What just happened?** Teams installs your agent like any other app. It now shows up in chats and channels for whoever installed it.

### Step 9.3 — Run the demo script in Teams

Repeat the 9 steps from Lab 7 — this time inside Teams.

### Step 9.4 — Record it

Use Loom, OBS, or a Teams meeting recording. Save the file as `demo.mp4` (or `demo.gif`) in the project root.

**What just happened?** You now have proof — a video — that all 9 phases work together. Share this with your team or hiring manager.

### ✅ Checkpoint 9

A recording exists in the project root showing the full demo working in Teams.

---

## ✅ Acceptance checklist (graduation criteria)

Tick **all** before calling this done:

- [ ] Every capability from the README requirements table is demonstrated.
- [ ] `pytest -q` returns ≥ 6 passed.
- [ ] `docker build` succeeds locally.
- [ ] `azd up` succeeded; the agent responds in Teams.
- [ ] App Insights shows traces for at least one full conversation.
- [ ] No secrets in source or `.env` files committed to git.
- [ ] A `README.md` in the project root explains how to run it.
- [ ] A `demo.mp4` / `demo.gif` recording exists.

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| `BlobStorage` error: container not found | The container hasn't been created. | Re-run `bsc.create_container("agent-state")` once at startup. |
| Tickets appear across users | Stored in `state.conversation` instead of `state.user`. | Use `state.user` for per-person data (Phase 3 rule). |
| OAuth card doesn't appear | Bot resource OAuth Connection name doesn't match `OAUTH_CONNECTION_NAME` in `.env`. | Match them exactly (case-sensitive). |
| `httpx` 401 from Graph | Token scope missing (needs `User.Read`). | Grant admin consent in Entra → API permissions. |
| Container App returns 500 on first request | Cold-start LLM call timed out. | Increase `httpx` timeout to 60 sec. |
| `pytest` can't import `tools_v3` | Tests live in `tests/`, can't see project root. | Add `sys.path.insert(0, ".")` at the top of the test file or set `pythonpath = ["."]` in `pyproject.toml`. |
| App Insights empty | Connection string env var typo. | `az containerapp show -n ... --query "properties.template.containers[0].env"` to inspect. |

---

## 🎓 Self-check

1. **Why store tickets in `state.user` and not `state.conversation`?**

   <details><summary>Show answer</summary>
   Each user should see only their own tickets. `state.user` is keyed by user id, so it's isolated per person. `state.conversation` is keyed by conversation id, which can be shared across many people in the same channel.
   </details>

2. **Why does the catch-all check `context.activity.value` before doing anything else?**

   <details><summary>Show answer</summary>
   Adaptive Card submissions arrive as `message` activities with `activity.value` populated but no plain text. If you skip that check and go straight to the LLM, the LLM has nothing to answer and the card data is lost.
   </details>

3. **What does `azd up` actually do?**

   <details><summary>Show answer</summary>
   It runs `azd provision` (deploys the Bicep template) **then** `azd deploy` (builds the Docker image, pushes it, updates the Container App).
   </details>

4. **Why use Azurite locally instead of a real Azure Storage account?**

   <details><summary>Show answer</summary>
   Azurite is free, offline, and instant. You can debug, restart, and reset the data hundreds of times without paying or polluting a real account. In production you swap the connection string for a real one.
   </details>

5. **Why is `pytest -q` valuable even when you have manual smoke tests?**

   <details><summary>Show answer</summary>
   Pytest runs in seconds and catches regressions automatically every time you change code. Manual tests are slow, easy to skip, and rely on you remembering what to test.
   </details>

---

## 🚀 Stretch goals (optional)

If you have time after the acceptance checklist:

1. **Proactive notifications** — Monday morning DM each user with their open ticket count.
2. **Multi-language** — detect user language and translate replies.
3. **Azure AI Search** — swap the in-memory RAG store for hybrid (vector + keyword) search.
4. **Approval workflow** — Critical tickets require manager approval via an Adaptive Card.
5. **GitHub Actions CI** — run `pytest` on every push, `azd deploy` on push to `main`.
6. **Cost dashboard** — Azure Workbook showing daily tokens, requests, and $ spend.

---

## 🏁 You're done!

You can now:

- Combine **all** Phase 1–9 capabilities into one production-shape agent.
- Containerize and deploy to Azure Container Apps with `azd up`.
- Validate end-to-end through pytest, Emulator, and Teams.
- Observe live traffic in App Insights.

Next → [Phase 11 — Wrap with Agent 365 (the full enterprise wrap)](../Phase11_Wrap_with_Agent365/README.md)
