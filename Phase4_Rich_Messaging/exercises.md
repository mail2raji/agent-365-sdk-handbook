# 🧪 Phase 4 — Hands-On Lab: Build a Leave-Request Form with Adaptive Cards

> A step-by-step lab. By the end you'll send a real interactive form (with text boxes, date pickers, and a Submit button) inside a chat, and read the user's answer back in code.

---

## 🎯 What you'll build today

A small but realistic agent called **`leave_request_agent`**:

1. When the user types `request leave`, the agent sends an **Adaptive Card form** with: reason, start date, end date, and a leave-type dropdown.
2. When the user clicks **Submit**, the agent receives the form data, assigns a request id (e.g. `LR-A1B2C3`), and sends a **confirmation card** back.
3. The submitted requests are stored in conversation state (carried over from Phase 3).

You'll also learn:

- The 7 most useful Adaptive Card elements.
- How to load a JSON template at runtime.
- How to inspect what `activity.value` looks like when a card is submitted.

> 👶 Imagine Adaptive Cards as **paper forms** the chatbot hands you inside the chat. You fill in the boxes, click Submit, and your filled-in form magically lands in the bot's hands.

⏱️ **About 75 minutes**.

---

## ✅ Before you start

- [ ] Phase 3 finished — you understand `state.conversation`.
- [ ] Terminal prompt starts with **`(.venv)`**.
- [ ] You have a modern browser open and can visit <https://adaptivecards.io/designer/>.

---

## 🗺️ Today's roadmap

```
Lab 1 → Tour adaptivecards.io/designer and copy a JSON card
Lab 2 → Send your first card from Python
Lab 3 → Build the leave-request form and read submissions
Lab 4 → Send a confirmation card back
Lab 5 → Show submitted requests stored in state
```

---

## Lab 1 — Tour the Adaptive Cards designer (~10 min)

**You will:** see how cards are built visually, then copy the JSON.

### Step 1.1 — Open the designer

Browse to <https://adaptivecards.io/designer/>.

You'll see a 3-pane UI:

- **Left** — Card elements (TextBlock, Input.Text, …).
- **Middle** — Preview.
- **Right** — Card JSON.

### Step 1.2 — Pick a sample

Top-left dropdown: **Select sample → "Input form"**. The preview now shows a fancy form.

The **right pane** shows the JSON. It starts with:

```json
{
  "type": "AdaptiveCard",
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "version": "1.5",
  "body": [ ... ],
  "actions": [ ... ]
}
```

> 🧠 **The whole "card" is just a dict.** It has a `body` (the visual elements) and `actions` (the buttons). Nothing magic — we'll build dicts like this in Python.

### Step 1.3 — The 7 elements you'll use most

| Element | What it is | Important property |
|---|---|---|
| `TextBlock` | Static text | `text`, `size`, `weight`, `wrap` |
| `Input.Text` | Text box (single or multi-line) | `id`, `label`, `isMultiline` |
| `Input.Number` | Numeric input | `id`, `min`, `max` |
| `Input.Date` | Date picker | `id` |
| `Input.ChoiceSet` | Dropdown / radio | `id`, `choices`, `style` |
| `Action.Submit` | Submit button (sends form back) | `title`, `data` |
| `Action.OpenUrl` | Opens a URL | `title`, `url` |

Every `Input.*` needs an `id` — that's the **key** the form data will arrive under when the user submits.

**What just happened?** You learned that an Adaptive Card is just a recipe (`body` + `actions`) in JSON. Once you know the 7 elements, you can build any form a manager could ever ask for — surveys, approvals, tickets — without writing a single line of UI code.

### ✅ Checkpoint 1
You've seen the designer, you understand a card is just JSON with `body` + `actions`, and you know the 7 elements.

---

## Lab 2 — Send your first card from Python (~15 min)

**You will:** create a tiny "Hello card" agent.

### Step 2.1 — Make the lab folder

```powershell
cd Phase4_Rich_Messaging
mkdir -Force lab_cards
cd lab_cards
Copy-Item ..\code\leave_request_agent\start_server.py .
```

### Step 2.2 — Create `hello_card.py`

```powershell
New-Item hello_card.py -ItemType File
code hello_card.py
```

Paste:

```python
"""hello_card.py — sends one Adaptive Card with a TextBlock and a button."""
from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from microsoft_agents.activity import Activity, ActivityTypes, Attachment
from start_server import start_server

ADAPTIVE_CARD = "application/vnd.microsoft.card.adaptive"

AGENT_APP = AgentApplication(storage=MemoryStorage())


def hello_card() -> dict:
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "size": "Large", "weight": "Bolder",
             "text": "👋 Hello from your agent!"},
            {"type": "TextBlock", "text": "This is your first Adaptive Card."},
        ],
        "actions": [
            {"type": "Action.OpenUrl", "title": "Learn more",
             "url": "https://adaptivecards.io"},
        ],
    }


@AGENT_APP.message("card")
async def send_card(context: TurnContext, state: TurnState):
    await context.send_activity(Activity(
        type=ActivityTypes.MESSAGE,
        attachments=[Attachment(content_type=ADAPTIVE_CARD, content=hello_card())],
    ))


@AGENT_APP.activity("message")
async def fallback(context, state):
    await context.send_activity("Type `card` to receive an Adaptive Card.")


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

Save.

### Step 2.3 — Run & send

```powershell
python hello_card.py
```

In terminal 2 (with the `Send-Msg` function from earlier phases):

```powershell
Send-Msg "card"
```

You won't see the card visually (no UI yet — Phase 7 shows that in Teams). But terminal 1 should show the outgoing activity in the SDK logs **without errors**, which is enough to prove the JSON is valid.

### Step 2.4 — Inspect the outgoing card

Replace the `send_card` body with a version that also prints the JSON:

```python
@AGENT_APP.message("card")
async def send_card(context: TurnContext, state: TurnState):
    import json
    card = hello_card()
    print("---- OUTGOING CARD ----")
    print(json.dumps(card, indent=2))
    print("-----------------------")
    await context.send_activity(Activity(
        type=ActivityTypes.MESSAGE,
        attachments=[Attachment(content_type=ADAPTIVE_CARD, content=card)],
    ))
```

Restart, send `card` again — you'll see the JSON in terminal 1.

> 💡 **Tip:** copy the JSON back into <https://adaptivecards.io/designer/> ("New card → paste your JSON") to *see* what your card looks like rendered. This is the fastest design loop.

**What just happened?** You established the **print + designer loop**: print the JSON your code emits, paste it into the visual designer, and you can see *exactly* what the user sees — without setting up Teams. Use this loop every time you build a new card.

### ✅ Checkpoint 2
The agent accepts `card`, prints a JSON card, and doesn't error. You can paste that JSON into the designer to preview it.

Stop the agent.

---

## Lab 3 — Build the leave-request form (~15 min)

**You will:** build the real form: reason + 2 dates + dropdown + submit.

### Step 3.1 — Create `app.py`

```powershell
New-Item app.py -ItemType File
code app.py
```

Paste:

```python
"""app.py — Leave-Request agent with two cards."""
from __future__ import annotations
import uuid
from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from microsoft_agents.activity import Activity, ActivityTypes, Attachment
from start_server import start_server

ADAPTIVE_CARD = "application/vnd.microsoft.card.adaptive"
AGENT_APP = AgentApplication(storage=MemoryStorage())


def build_leave_form() -> dict:
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "size": "Large", "weight": "Bolder",
             "text": "📝 Request Time Off"},
            {"type": "Input.Text", "id": "reason", "label": "Reason",
             "placeholder": "Why are you taking leave?", "isRequired": True,
             "errorMessage": "Please provide a reason."},
            {"type": "Input.Date", "id": "start", "label": "Start date",
             "isRequired": True},
            {"type": "Input.Date", "id": "end", "label": "End date",
             "isRequired": True},
            {"type": "Input.ChoiceSet", "id": "leave_type", "label": "Type",
             "style": "compact", "value": "vacation",
             "choices": [
                {"title": "Vacation", "value": "vacation"},
                {"title": "Sick", "value": "sick"},
                {"title": "Personal", "value": "personal"},
            ]},
        ],
        "actions": [
            {"type": "Action.Submit", "title": "Submit",
             "data": {"action": "submit_leave"}},
        ],
    }


def build_confirmation(request_id: str, data: dict) -> dict:
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "size": "Large", "weight": "Bolder",
             "text": f"✅ Request {request_id} submitted"},
            {"type": "FactSet", "facts": [
                {"title": "Reason", "value": data.get("reason", "")},
                {"title": "Start", "value": data.get("start", "")},
                {"title": "End", "value": data.get("end", "")},
                {"title": "Type", "value": data.get("leave_type", "")},
            ]},
            {"type": "TextBlock", "text": "Your manager has been notified.",
             "isSubtle": True, "wrap": True},
        ],
    }


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity("Type `request leave` to open the form.")


@AGENT_APP.message("request leave")
async def show_form(context: TurnContext, state: TurnState):
    await context.send_activity(Activity(
        type=ActivityTypes.MESSAGE,
        attachments=[Attachment(content_type=ADAPTIVE_CARD,
                                content=build_leave_form())],
    ))


@AGENT_APP.activity("message")
async def on_any(context: TurnContext, state: TurnState):
    # Did the user submit a card?
    if context.activity.value:
        data = dict(context.activity.value)
        print("---- SUBMITTED VALUES ----")
        print(data)
        print("--------------------------")
        if data.get("action") == "submit_leave":
            req_id = f"LR-{uuid.uuid4().hex[:6].upper()}"
            # Save in state
            requests = state.conversation.get("requests", [])
            requests.append({"id": req_id, **data})
            state.conversation["requests"] = requests

            await context.send_activity(Activity(
                type=ActivityTypes.MESSAGE,
                attachments=[Attachment(content_type=ADAPTIVE_CARD,
                                        content=build_confirmation(req_id, data))],
            ))
            await context.send_activity(f"Your request id is **{req_id}**.")
            return

    # Plain text fallback
    await context.send_activity(
        "Try `request leave` to open the form, or `my requests` to list yours."
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

Save.

### Step 3.2 — Run

```powershell
python app.py
```

### Step 3.3 — Trigger the form

In terminal 2:

```powershell
Send-Msg "request leave"
```

Terminal 1 should show that an activity was sent with the card attachment.

### Step 3.4 — Simulate a card submission

When a real user clicks Submit in Teams, the channel sends a `message` activity where `activity.value` contains the form values. We can fake that:

```powershell
$body = @{
    type="message"; text=""
    value=@{
        action="submit_leave"
        reason="Family wedding"
        start="2026-07-10"
        end="2026-07-15"
        leave_type="vacation"
    }
    from=@{id="alice"; name="Alice"}; recipient=@{id="bot"}
    conversation=@{id="alice-1"}; serviceUrl="http://localhost"
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages `
    -Method POST -ContentType "application/json" -Body $body
```

Terminal 1 should print:

```text
---- SUBMITTED VALUES ----
{'action': 'submit_leave', 'reason': 'Family wedding', ...}
--------------------------
```

🎉 You've successfully received form data.

**What just happened?** You closed the **round trip**: agent shows form → user fills it → channel posts back as a `message` with `activity.value` — the SDK turns it into a Python dict. From there it's just normal Python: validate, save, reply.

### ✅ Checkpoint 3
Sending the fake submission prints the values in terminal 1 and the agent saves the request in state.

---

## Lab 4 — Show the confirmation card (~10 min)

**You will:** verify the receipt card the agent already returns after every submission, and visually confirm it renders cleanly.

The code above already sends a confirmation card. Let's verify it works.

### Step 4.1 — Trigger another submission with different data

```powershell
$body = @{
    type="message"; text=""
    value=@{
        action="submit_leave"; reason="Doctor"
        start="2026-08-01"; end="2026-08-01"; leave_type="sick"
    }
    from=@{id="alice"; name="Alice"}; recipient=@{id="bot"}
    conversation=@{id="alice-1"}; serviceUrl="http://localhost"
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages `
    -Method POST -ContentType "application/json" -Body $body
```

The response includes two outgoing activities: the confirmation **card** and a text line `Your request id is **LR-XXXXXX**.`

### Step 4.2 — Visually verify in the designer

Grab the printed `OUTGOING CARD` JSON from terminal 1 (you can add a `print` to `build_confirmation` if you want), paste into <https://adaptivecards.io/designer/> "Open file → paste JSON". You'll see the rendered card.

**What just happened?** Every submission now produces a unique `LR-...` id and a printable receipt. That id can later be passed to a ticketing system, Outlook email, or downstream API — cards become your front door to **any** business process.

### ✅ Checkpoint 4
Two submissions produce two unique `LR-…` ids, and the confirmation card structure is well-formed (no designer warnings).

---

## Lab 5 — List the user's requests (~10 min)

**You will:** add a `my requests` command that shows what's in state.

### Step 5.1 — Add the handler

In `app.py`, **before** `on_any`, insert:

```python
@AGENT_APP.message("my requests")
async def my_requests(context: TurnContext, state: TurnState):
    requests = state.conversation.get("requests", [])
    if not requests:
        await context.send_activity("You haven't submitted any requests yet.")
        return
    lines = [f"- **{r['id']}**: {r['reason']} ({r['start']} → {r['end']}, {r['leave_type']})"
             for r in requests]
    await context.send_activity("📋 Your requests:\n" + "\n".join(lines))
```

Save & restart.

### Step 5.2 — Submit two requests then list them

```powershell
# request 1
$body = @{
    type="message"; text=""
    value=@{action="submit_leave"; reason="Wedding"; start="2026-07-10"; end="2026-07-15"; leave_type="vacation"}
    from=@{id="alice"; name="Alice"}; recipient=@{id="bot"}
    conversation=@{id="alice-1"}; serviceUrl="http://localhost"
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages -Method POST -ContentType "application/json" -Body $body

# request 2
$body = @{
    type="message"; text=""
    value=@{action="submit_leave"; reason="Doctor"; start="2026-08-01"; end="2026-08-01"; leave_type="sick"}
    from=@{id="alice"; name="Alice"}; recipient=@{id="bot"}
    conversation=@{id="alice-1"}; serviceUrl="http://localhost"
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages -Method POST -ContentType "application/json" -Body $body

# list
Send-Msg "my requests" -User alice
```

You should get back:

```text
📋 Your requests:
- **LR-XXXXXX**: Wedding (2026-07-10 → 2026-07-15, vacation)
- **LR-YYYYYY**: Doctor (2026-08-01 → 2026-08-01, sick)
```

**What just happened?** Combining Phase 3's state with Phase 4's cards = a real micro-app: users submit data with a form, the agent persists it, and they can browse history. Every internal tool you'll ever build is essentially this same loop — just with prettier cards.

### ✅ Checkpoint 5
Listing returns the same number of requests you submitted.

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| `activity.value` is `None` when you expect form data | You sent the wrong JSON shape — `value` must be at the top level. | Use the PowerShell snippets in Lab 3.4 (with `value=@{...}` at top level). |
| The card renders broken in the designer | Invalid Adaptive Cards version or unknown property. | Bump `"version": "1.5"`; remove unsupported properties. |
| `KeyError: 'reason'` in `build_confirmation` | The form sent no `reason` — maybe the user skipped a non-required field. | Use `data.get("reason", "")` (already in the example). |
| Multiple bot replies after one submit | The catch-all and a specific handler both ran. | The pattern in `on_any` `return`s after sending the confirmation — make sure you didn't lose the `return`. |
| `TypeError: cannot pickle ...` when state saves | You put a non-serializable object (like a `datetime`) into state. | Convert to ISO string with `dt.isoformat()` before saving. |

---

## 🎓 Self-check

1. **What's an Adaptive Card, in one sentence?**

   <details><summary>Show answer</summary>
   A JSON document the channel renders as a small UI inside the chat. Same JSON looks like a Teams card in Teams, an Outlook card in email, etc.
   </details>

2. **What's the magic `content_type` for Adaptive Card attachments?**

   <details><summary>Show answer</summary>
   `application/vnd.microsoft.card.adaptive`
   </details>

3. **When the user clicks `Action.Submit`, where does the form data arrive in your handler?**

   <details><summary>Show answer</summary>
   On `context.activity.value` — a dict whose keys are the `id` of each `Input.*` element.
   </details>

4. **Why do all `Input.*` elements need an `id`?**

   <details><summary>Show answer</summary>
   The `id` becomes the dict key when the form is submitted. No id → the value never reaches your code.
   </details>

5. **How would you make the "reason" field required?**

   <details><summary>Show answer</summary>
   Add `"isRequired": true` and `"errorMessage": "Please provide a reason."` to the `Input.Text` definition.
   </details>

---

## 🚀 Bonus tasks

1. **Server-side validation** — reject submissions where `end < start`. Send back an error message instead of the confirmation.
2. **Approve / Reject buttons** — on the confirmation card add two `Action.Submit` buttons with `data: {action: "approve_leave", id: "LR-..."}`. Build a manager-mode handler that updates the request status.
3. **Open the card in the designer** — copy the JSON and design a fancier look (banner, columns, icon).
4. **Reuse cards as templates** — move both card builders to `cards/leave.py` and import them.
5. **Save to a JSON file** — write each submission to `leave_requests.json` (instead of/in addition to state) so you have an audit trail.

---

## 🏁 You're done!

You can now:

- Read & write Adaptive Cards as Python dicts.
- Send a card from any handler.
- Read submitted form data from `context.activity.value`.
- Confirm submissions with a second card.

Next → [Phase 5 — LLM Integration (build an AI Study Buddy)](../Phase5_LLM_Integration/README.md)
