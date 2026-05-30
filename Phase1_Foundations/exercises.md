# 🧪 Phase 1 — Hands-On Lab: Build the Echo Agent

> A step-by-step lab. Follow each instruction in order. Don't skip steps. By the end, your computer will be a chat-bot that talks back.

---

## 🎯 What you'll build today

Two tiny agents you can actually chat with:

1. **`echo_agent`** — echoes whatever you type back to you. *(Lab 1–3)*
2. **`echo_plus`** — same agent, but with a greeting, a `/help` command, and a `clear` command. *(Lab 4)*

You'll also learn to:

- Read the JSON of an activity (so you can debug when things go wrong).
- Send the agent a fake message from PowerShell — no Teams needed.

> 👶 Think of it like making a parrot. First we build a parrot that just repeats you (`echo_agent`). Then we teach the parrot three magic words (`echo_plus`). All in your terminal.

⏱️ **About 60–75 minutes** if you take your time.

---

## ✅ Before you start (checklist)

- [ ] Phase 0 finished — running `python hello_sdk.py` in the Phase 0 folder prints "All SDK imports OK".
- [ ] Your terminal prompt starts with **`(.venv)`**. If not, run `.\.venv\Scripts\Activate.ps1` from the curriculum root.
- [ ] VS Code is open at `Agent365_SDK_Learning/`.

---

## 🗺️ Today's roadmap

```
Lab 1 → Open the prebuilt echo_agent and understand the 6 imports
Lab 2 → Run the agent locally
Lab 3 → Send it a message from PowerShell (no UI needed)
Lab 4 → Copy & extend it into echo_plus
Lab 5 → (Optional) Inspect activity JSON
```

---

## Lab 1 — Open the echo_agent and decode every line (~15 min)

**You will:** open the file that ships with this phase and we'll walk through every block.

### Step 1.1 — Move to the Phase 1 folder

In the terminal:

```powershell
cd Phase1_Foundations\code\echo_agent
```

> Already inside another phase folder? Type `cd ..\..\..\Phase1_Foundations\code\echo_agent` instead.

Check what's inside:

```powershell
Get-ChildItem
```

You should see at least:

```text
app.py
start_server.py
.env.example
```

### Step 1.2 — Open `app.py`

```powershell
code app.py
```

Your file should look exactly like this (if not, that's OK — just keep reading):

```python
from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from start_server import start_server

AGENT_APP = AgentApplication(storage=MemoryStorage())

@AGENT_APP.conversation_update("membersAdded")
async def on_join(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity("👋 Hi! I'm an echo bot. Type anything.")

@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"You said: {context.activity.text}")

if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

### Step 1.3 — Decode it block by block

| Lines | What they do | Plain English |
|---|---|---|
| `from microsoft_agents.hosting.core import …` | Pulls 4 classes from the SDK. | "Bring me these 4 tools from the cupboard." |
| `from start_server import start_server` | Pulls in the tiny web server (file lives next to `app.py`). | "Bring me the front door." |
| `AGENT_APP = AgentApplication(…)` | Creates the **brain**. | "Make me an empty agent that uses RAM for memory." |
| `@AGENT_APP.conversation_update("membersAdded")` | Registers a handler that fires when a new user joins. | "When someone walks in, say hi." |
| `@AGENT_APP.activity("message")` | Registers a handler that fires for every text message. | "When someone types, echo it back." |
| `start_server(AGENT_APP, None)` | Boots the web server on port 3978. | "Open the front door." |

> 🧠 The `@…` lines are called **decorators**. Read them as: "the next function is a handler — please call it when *this* happens."

**What just happened?** You read the entire agent in 20 lines. It's literally a tiny web server + a brain + two helpers (one for hello, one for messages). Everything else in this curriculum is built on top of these 4 imports — so don't panic when later phases look bigger, the core is always this small.

### ✅ Checkpoint 1
You can point to (a) the brain (`AgentApplication`), (b) the welcome handler, (c) the message handler, and (d) the line that starts the server.

---

## Lab 2 — Run the agent (~5 min)

**You will:** start the agent and confirm it's listening on port 3978.

### Step 2.1 — Run it

Still in `Phase1_Foundations\code\echo_agent`:

```powershell
python app.py
```

**Expected output (give it 1–2 seconds):**

```text
======== Running on http://localhost:3978 ========
(Press CTRL+C to quit)
```

If you see this — congratulations, your computer is now a chat server.

### Step 2.2 — Confirm the front door is open

Open a **second terminal** (`Ctrl+Shift+\``). In the new terminal:

```powershell
Test-NetConnection localhost -Port 3978
```

You want to see `TcpTestSucceeded : True`.

On macOS/Linux instead:

```bash
nc -zv localhost 3978
```

**What just happened?** Your laptop is now a chat server. Port 3978 is the "front door" — anyone who knows the address can knock. In the next lab we'll be the visitor knocking from terminal 2.

### ✅ Checkpoint 2
Terminal 1 shows `Running on http://localhost:3978`. Terminal 2 confirms port 3978 is open.

> ❗ Keep terminal 1 running. You'll send messages to it from terminal 2 in the next lab. If you accidentally pressed `Ctrl+C`, just re-run `python app.py`.

---

## Lab 3 — Talk to the agent from PowerShell (~10 min)

**You will:** send the agent a fake chat message using `Invoke-RestMethod`. No Teams, no browser — just text.

### Step 3.1 — Why are we doing this?

The agent's "front door" is the URL `http://localhost:3978/api/messages`. In production, **Teams** or **Web Chat** sends JSON-formatted activity objects to that URL. We can pretend to be Teams by sending our own JSON with PowerShell.

### Step 3.2 — Build the fake message

In **terminal 2**, paste this **all at once**:

```powershell
$body = @{
    type         = "message"
    text         = "hello agent"
    from         = @{ id = "user-1"; name = "Lab User" }
    recipient    = @{ id = "bot"; name = "Echo Bot" }
    conversation = @{ id = "chat-1" }
    serviceUrl   = "http://localhost"
    channelId    = "emulator"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri http://localhost:3978/api/messages `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

Press Enter.

**Expected output in terminal 2:** *(nothing visible — `Invoke-RestMethod` returns silently when the server replies 200 OK)*

**Expected output in terminal 1:** a log line per request, no errors.

### Step 3.3 — Where did the echo go?

The reply is in the HTTP response (look at terminal 1 logs), but for a quick sanity check let's intercept it.

Stop the agent in terminal 1 (`Ctrl+C`). Open `app.py` and add **one print line** so we see the message arriving:

```python
@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    print(f"[RECEIVED] {context.activity.text}")        # ← add this
    await context.send_activity(f"You said: {context.activity.text}")
```

Save (`Ctrl+S`). Re-run:

```powershell
python app.py
```

Now in terminal 2, send the message again:

```powershell
Invoke-RestMethod -Uri http://localhost:3978/api/messages `
    -Method POST -ContentType "application/json" -Body $body
```

In terminal 1 you should see:

```text
[RECEIVED] hello agent
```

**What just happened?** You faked a Teams message using PowerShell. The agent didn't know (or care) you weren't real Teams — it just saw JSON arrive at `/api/messages`. This trick is **gold** for debugging: you can replay any bug with a saved JSON snippet instead of clicking through Teams every time.

### ✅ Checkpoint 3
Terminal 1 prints `[RECEIVED] hello agent` whenever you send a message from terminal 2.

> 🧠 Why `[RECEIVED]` and not `You said:`? The `You said:` text is sent as a *response* back to the channel — it never goes to stdout. The `print(...)` line we added is the one that hits the console.

---

## Lab 4 — Build `echo_plus` from scratch (~20 min)

**You will:** copy `echo_agent` into a new folder called `echo_plus` and add three commands:

| Command the user types | What the agent does |
|---|---|
| `/help` | Lists the commands |
| `clear` | Tells the user "Nothing to clear yet — Phase 3 will fix that 😉" |
| anything else | Echoes back with a counter: `[#3] You said: …` |

### Step 4.1 — Copy the folder

Stop the running agent (terminal 1: `Ctrl+C`). Then:

```powershell
cd ..
Copy-Item -Recurse echo_agent echo_plus
cd echo_plus
code app.py
```

### Step 4.2 — Replace `app.py` with this

Select everything in `app.py` (`Ctrl+A`) and paste this:

```python
"""echo_plus — Phase 1 lab: an echo agent with /help and a counter."""
from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from start_server import start_server

AGENT_APP = AgentApplication(storage=MemoryStorage())

# We use a plain module-level counter for now. Phase 3 teaches us the
# *correct* way (state). For one user on localhost this is fine.
_count = 0

HELP_TEXT = (
    "Commands I understand:\n"
    "  /help   – show this list\n"
    "  clear   – (placeholder) reset memory\n"
    "  <text>  – I'll echo it back with a counter"
)


@AGENT_APP.conversation_update("membersAdded")
async def on_join(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "👋 Hi! I'm echo_plus.\n" + HELP_TEXT
            )


# Handler #1 — exact-text match "/help"
@AGENT_APP.message("/help")
async def on_help(context: TurnContext, state: TurnState):
    await context.send_activity(HELP_TEXT)


# Handler #2 — exact-text match "clear"
@AGENT_APP.message("clear")
async def on_clear(context: TurnContext, state: TurnState):
    await context.send_activity(
        "🧹 Nothing to clear yet — Phase 3 will fix that 😉"
    )


# Handler #3 — catch-all for any other text
@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    global _count
    _count += 1
    print(f"[#{_count}] received: {context.activity.text}")
    await context.send_activity(f"[#{_count}] You said: {context.activity.text}")


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

Save (`Ctrl+S`).

### Step 4.3 — Decode the new pieces

- `@AGENT_APP.message("/help")` is a **specialised** decorator. It only fires when the **entire** message text equals `/help`. It runs *before* the catch-all because the SDK matches more specific handlers first.
- `_count` is a **global** Python variable — terrible for production (every user shares it!), but fine to see the difference between *no state* (here) and *real state* (Phase 3).

### Step 4.4 — Run & test

```powershell
python app.py
```

In terminal 2, send three messages with these `$body` values. Just replace the `text = …` line in the snippet and re-run `Invoke-RestMethod` for each:

```powershell
# Message 1
$body = @{ type="message"; text="/help"; from=@{id="u1"}; recipient=@{id="b"}; conversation=@{id="c1"}; serviceUrl="http://localhost" } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages -Method POST -ContentType "application/json" -Body $body

# Message 2
$body = @{ type="message"; text="hello"; from=@{id="u1"}; recipient=@{id="b"}; conversation=@{id="c1"}; serviceUrl="http://localhost" } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages -Method POST -ContentType "application/json" -Body $body

# Message 3
$body = @{ type="message"; text="clear"; from=@{id="u1"}; recipient=@{id="b"}; conversation=@{id="c1"}; serviceUrl="http://localhost" } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages -Method POST -ContentType "application/json" -Body $body
```

**In terminal 1 you should see:**

```text
[#1] received: hello
```

(Note: `/help` and `clear` don't increment the counter because they are caught by their own specific handlers and `return` before the catch-all.)

**What just happened?** You learned the **most important rule** of agent handlers: **specific beats general**. Exact-text handlers (`/help`, `clear`) win over the catch-all (`activity("message")`). The SDK does this automatically — your job is just to register the handler at the right specificity level.

### ✅ Checkpoint 4
- `/help` returns the command list.
- `clear` returns the placeholder line.
- Any other text returns an echo with `[#1]`, `[#2]`, … incrementing.

---

## Lab 5 — (Optional) Inspect the JSON of a real activity (~10 min)

**You will:** print the full incoming activity to see all 25+ fields the channel sends.

### Step 5.1 — Add an inspector

In `echo_plus/app.py`, replace the catch-all `on_message` with:

```python
@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    global _count
    _count += 1
    # 👇 Dump the full activity for inspection
    print("---- INCOMING ACTIVITY ----")
    print(context.activity.model_dump_json(indent=2))
    print("---------------------------")
    await context.send_activity(f"[#{_count}] You said: {context.activity.text}")
```

Save. Restart (`Ctrl+C` then `python app.py`).

Send any message from terminal 2:

```powershell
$body = @{ type="message"; text="show me everything"; from=@{id="u1"; name="Alice"}; recipient=@{id="b"}; conversation=@{id="c1"}; serviceUrl="http://localhost"; channelId="emulator"; locale="en-US" } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages -Method POST -ContentType "application/json" -Body $body
```

In terminal 1 you'll see ~30 lines of JSON like:

```json
{
  "type": "message",
  "id": null,
  "timestamp": "2025-...",
  "text": "show me everything",
  "from": { "id": "u1", "name": "Alice" },
  "recipient": { "id": "b" },
  "conversation": { "id": "c1" },
  "channel_id": "emulator",
  "service_url": "http://localhost",
  "locale": "en-US",
  ...
}
```

**Why is this useful?** When something breaks in production (e.g. "Teams sent something weird"), copy that JSON into a comment and you can replay it with `Invoke-RestMethod`.

### ✅ Checkpoint 5
You can see the full activity JSON in terminal 1.

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| `Address already in use` on port 3978 | An older agent is still running. | Close the other terminal, or change port: edit `start_server.py` and look for `3978`. |
| `ModuleNotFoundError: microsoft_agents` | venv not active. | `.\.venv\Scripts\Activate.ps1` from the curriculum root, then run again. |
| `Invoke-RestMethod : The remote name could not be resolved` | You typed `localhost` wrong, or the server isn't running. | Check terminal 1 still says `Running on http://localhost:3978`. |
| `Invoke-RestMethod : 401 Unauthorized` | Auth is on but no token sent. | Set `ANONYMOUS_ALLOWED=true` in `.env`, then restart the agent (this is fine for local dev). |
| `Invoke-RestMethod : 415 Unsupported Media Type` | Forgot `-ContentType "application/json"`. | Add it. |
| Handler fires for the *wrong* message | Decorator ordering or wrong match type. | Exact-text `.message("foo")` beats catch-all `.activity("message")`. Regex needs `re.compile(...)`. |
| Nothing happens when you `python app.py` | The file has a typo and crashed silently — but you can't see it because there's no traceback. | Run `python -c "import app"` to see the import error. |

---

## 🎓 Self-check

1. **What is the difference between `@AGENT_APP.activity("message")` and `@AGENT_APP.message("hello")`?**

   <details><summary>Show answer</summary>
   The first runs for **every** message activity (catch-all). The second runs **only** when the message text is exactly `hello`. The SDK tries the more specific match first.
   </details>

2. **What does `MemoryStorage()` mean for our counter `_count`?**

   <details><summary>Show answer</summary>
   `MemoryStorage` keeps SDK state in RAM. But our `_count` isn't even using SDK state — it's a plain Python global. Both die the moment you stop the process. Phase 3 introduces real persistence.
   </details>

3. **In `on_join`, why do we check `m.id != context.activity.recipient.id`?**

   <details><summary>Show answer</summary>
   The `membersAdded` event fires for **everyone** added to the conversation — including the **bot itself**. Without that check the bot would greet itself the moment it joins a room.
   </details>

4. **Why does `clear` not increment the counter?**

   <details><summary>Show answer</summary>
   `@AGENT_APP.message("clear")` matches first and its handler `return`s without falling through to the catch-all. Specific beats general.
   </details>

5. **Name 3 fields you saw inside the incoming activity JSON.**

   <details><summary>Show answer</summary>
   Any 3 of: `type`, `text`, `from`, `recipient`, `conversation`, `channel_id`, `service_url`, `locale`, `timestamp`, …
   </details>

---

## 🚀 Bonus tasks

1. **Make the agent SHOUT** — wrap the echo in `.upper()` so `hello` comes back as `YOU SAID: HELLO`.
2. **Add a `time` command** that replies with the current time (`from datetime import datetime`).
3. **Add a regex handler** that catches anything starting with `weather` — for now reply "Weather in Phase 6 — coming soon".

   ```python
   import re
   @AGENT_APP.message(re.compile(r"^weather", re.IGNORECASE))
   async def stub(context, state):
       await context.send_activity("Weather in Phase 6 — coming soon 🌦️")
   ```

4. **Save 5 different test messages** as a PowerShell script `tests.ps1` so you can replay your scenario with one keypress.

---

## 🏁 You're done!

You now know:

- How to start an agent on port 3978.
- How to write three different kinds of handlers (`conversation_update`, exact-text `message`, catch-all `activity`).
- How to send a fake activity from PowerShell (priceless for debugging).
- How to inspect the full activity JSON.

Next → [Phase 2 — Activities & Handlers (build an FAQ Agent)](../Phase2_Activities_and_Handlers/README.md)
