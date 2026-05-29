# 🐤 Phase 1 — Foundations & Your First Agent

> **Goal**: Build an **Echo Agent** that replies with whatever you type. Understand every line.

**Duration**: ~60–90 minutes.
**Prerequisite**: Phase 0 complete (smoke test passes).

---

## 📚 What you'll learn

1. What an **Activity** is and why everything is one.
2. What a **TurnContext** is.
3. What an **AgentApplication** is and how decorators register handlers.
4. The minimum code to host an agent on `http://localhost:3978`.
5. How to test the agent without any chat client (using `curl`).

---

## 1️⃣ The Activity — the only object that matters

When *anything* happens (message, member joined, button clicked, file uploaded), the SDK wraps it in a JSON object called an **Activity**.

A simple incoming message Activity looks like this:

```json
{
  "type": "message",
  "text": "Hello!",
  "from": { "id": "u-123", "name": "Alice" },
  "recipient": { "id": "bot-1", "name": "MyAgent" },
  "conversation": { "id": "c-987" },
  "channelId": "msteams"
}
```

Important fields:

| Field | What it means |
|---|---|
| `type` | What kind of event: `message`, `conversationUpdate`, `event`, `invoke`, … |
| `text` | The actual text the user typed (for messages). |
| `from` | The **user** who sent it. |
| `recipient` | **Your agent** as seen by the channel. |
| `conversation.id` | A stable ID for this chat thread — use it as your state key. |
| `channelId` | Which channel sent it: `msteams`, `webchat`, `directline`, `emulator`, … |

> 👶 An Activity is like a sticky note. The `type` is the colour of the note. The other fields are written on the note.

---

## 2️⃣ The TurnContext — the briefcase

Each time an Activity arrives, the SDK builds a **`TurnContext`** object and hands it to your handler.

The `TurnContext` is your **briefcase for this one turn**. It contains:

- `context.activity` — the incoming Activity.
- `context.send_activity(...)` — call this to reply.
- `context.update_activity(...)` / `delete_activity(...)` — edit or delete messages.
- IDs you'll need: `context.activity.from_property.id`, `context.activity.conversation.id`.

Minimal handler:

```python
async def echo(context: TurnContext, state: TurnState):
    await context.send_activity(f"You said: {context.activity.text}")
```

`async`/`await` are required — the SDK is built on `asyncio`.

---

## 3️⃣ The AgentApplication — the wiring panel

The `AgentApplication` is the central object that:

- Owns the **storage** (memory or Cosmos DB or blob).
- Owns the **adapter** (CloudAdapter — talks HTTP).
- Holds **routes** — your `@app.message(...)` / `@app.activity(...)` / `@app.conversation_update(...)` handlers.

Creating one is just:

```python
from microsoft_agents.hosting.core import AgentApplication, MemoryStorage

AGENT_APP = AgentApplication(storage=MemoryStorage())
```

You then decorate functions:

```python
@AGENT_APP.message("/help")
async def on_help(context, state):
    await context.send_activity("I can echo what you say. Try anything.")
```

`/help` matches the **exact text** (case-insensitive). For pattern matching, pass a `re.compile(...)` object.

---

## 4️⃣ Where messages come in — `CloudAdapter` + `start_server`

The actual HTTP server is provided by the **aiohttp hosting** package:

```python
from microsoft_agents.hosting.aiohttp import CloudAdapter
from start_server import start_server         # tiny helper shown below
```

`start_server` launches `aiohttp` on **port 3978** and wires `POST /api/messages` to call your `AGENT_APP`.

You don't have to write `start_server` from scratch — but for transparency we provide a 20-line version in [code/echo_agent/start_server.py](code/echo_agent/start_server.py).

---

## 5️⃣ Build the Echo Agent (step by step)

Open the folder `Phase1_Foundations/code/echo_agent/`. We will walk through every file.

### File 1 — `start_server.py` (the plumbing)

```python
# start_server.py
"""Tiny aiohttp server that hosts an AgentApplication.

You will almost never modify this file. It exists so you can see the
plumbing once. From Phase 2 onward we just import it.
"""
from __future__ import annotations

import os
import logging
from aiohttp import web
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import AgentApplication

logger = logging.getLogger(__name__)


def start_server(agent_app: AgentApplication, adapter: CloudAdapter | None = None) -> None:
    """Start an HTTP server hosting `agent_app` on port 3978."""
    if adapter is None:
        adapter = CloudAdapter()

    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, agent_app)

    app = web.Application()
    app.router.add_post("/api/messages", messages)

    port = int(os.environ.get("PORT", 3978))
    logger.info(f"Listening on http://localhost:{port}/api/messages")
    web.run_app(app, host="localhost", port=port)
```

**Line by line:**

- `CloudAdapter()` creates the HTTP↔Activity translator. With no arguments it picks up auth settings from `.env`.
- `messages(req)` is the single endpoint. It calls `adapter.process(req, agent_app)` which:
  1. Reads the JSON body.
  2. Builds an `Activity`.
  3. Builds a `TurnContext`.
  4. Asks `AgentApplication` to find the matching handler and run it.
- `app.router.add_post("/api/messages", messages)` registers the URL.
- `web.run_app(...)` blocks forever, serving requests.

### File 2 — `app.py` (your agent's brain)

```python
# app.py
"""Echo Agent — Phase 1 sample.

What it does:
- Says "Welcome!" when a user joins.
- Replies with the help text if the user types "/help".
- Echoes anything else.
"""
from __future__ import annotations

import logging

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from start_server import start_server

# 1. Configure logging so you can see what's happening
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("echo_agent")

# 2. Create the agent. MemoryStorage = forget everything on restart (OK for dev).
AGENT_APP = AgentApplication(storage=MemoryStorage())


# 3. Greet new members
@AGENT_APP.conversation_update("membersAdded")
async def on_member_joined(context: TurnContext, state: TurnState) -> None:
    for member in context.activity.members_added or []:
        # Don't greet the bot itself
        if member.id != context.activity.recipient.id:
            await context.send_activity(
                f"👋 Welcome, {member.name or 'friend'}! Type anything and I'll echo it. Type /help for help."
            )


# 4. Respond to the literal text "/help"
@AGENT_APP.message("/help")
async def on_help(context: TurnContext, state: TurnState) -> None:
    await context.send_activity(
        "I'm a simple echo agent.\n"
        "- Type anything → I'll repeat it.\n"
        "- Type /help → you'll see this message."
    )


# 5. Catch-all: any message activity that didn't match anything above
@AGENT_APP.activity("message")
async def on_any_message(context: TurnContext, state: TurnState) -> None:
    text = context.activity.text or "(empty message)"
    logger.info(f"Echoing back: {text!r}")
    await context.send_activity(f"You said: {text}")


# 6. Start the server (blocks forever)
if __name__ == "__main__":
    try:
        start_server(AGENT_APP, None)
    except Exception as error:
        logger.exception("Server crashed")
        raise
```

**Why the order of decorators matters**

The SDK checks the **more specific** routes first:

1. `@AGENT_APP.message("/help")` — exact string match → wins for "/help"
2. `@AGENT_APP.activity("message")` — catches every other message

If you put the catch-all first, "/help" would never reach `on_help`. Specific → general.

### File 3 — `.env`

In the same folder, create `.env`:

```dotenv
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED=True
```

That single line tells the `CloudAdapter`: *"This is local dev — don't require a real auth token."*

---

## 6️⃣ Run it!

```powershell
cd Agent365_SDK_Learning\Phase1_Foundations\code\echo_agent
python app.py
```

You should see:

```
======== Running on http://localhost:3978 ========
(Press CTRL+C to quit)
```

The agent is listening. But how do we *send* it a message without Teams?

---

## 7️⃣ Test it with `curl`

The SDK accepts a normal HTTP `POST` to `/api/messages` with an Activity JSON body. Open a **second** terminal and run:

```powershell
$body = @{
  type = "message"
  text = "Hello agent!"
  from = @{ id = "user-1"; name = "Alice" }
  recipient = @{ id = "bot-1"; name = "EchoAgent" }
  conversation = @{ id = "conv-1" }
  serviceUrl = "http://localhost:3978"
  channelId = "emulator"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:3978/api/messages" -Method Post -Body $body -ContentType "application/json"
```

In the **agent terminal** you'll see:

```
INFO echo_agent: Echoing back: 'Hello agent!'
```

For a *real* round-trip experience with cards, attachments, etc. you'll use the **Agents Playground** or **Bot Framework Emulator** in Phase 9 — that gives you a chat UI.

---

## 8️⃣ Common gotchas

| Symptom | Fix |
|---|---|
| `address already in use` on port 3978 | Another agent is still running. Close it, or set `PORT=3979` in `.env`. |
| `401 Unauthorized` from the agent | Missing `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED=True` in `.env`. |
| Handler never fires | Check **decorator specificity** — a broader handler above may be swallowing the message. |
| `AttributeError: 'NoneType' object has no attribute 'text'` | The user sent a non-message activity (e.g. `typing`). Always guard with `context.activity.text or ""`. |

---

## ✅ Phase 1 checklist

- [ ] You can explain what an Activity is.
- [ ] You can explain what TurnContext is.
- [ ] You can name three decorators on AgentApplication.
- [ ] `python app.py` runs the Echo Agent on port 3978.
- [ ] A `curl` POST gets an echo response.
- [ ] You completed [exercises.md](exercises.md).

Next → [Phase 2 — Activities and Handlers](../Phase2_Activities_and_Handlers/README.md)
