# 🎴 Phase 4 — Adaptive Cards & Rich Messaging

> **Goal**: Send beautiful interactive cards (buttons, text inputs, date pickers). Build a **Leave-Request Approval** card.

**Duration**: ~75 minutes.

---

## 📚 What you'll learn

1. What an Adaptive Card actually is (it's just JSON).
2. The most useful card elements: `TextBlock`, `Input.Text`, `Input.Date`, `Input.ChoiceSet`, `Action.Submit`, `Action.OpenUrl`.
3. How to attach a card to a message.
4. How to read the form data the user submits back.

---

## 1️⃣ What is an Adaptive Card?

An **Adaptive Card** is a JSON document that channels (Teams, Outlook, web chat) render as a small UI inside the chat.

You don't draw pixels. You describe **what** you want; the channel renders it natively. The same JSON looks like a Teams card in Teams, an HTML widget in web chat, an email card in Outlook.

> 👶 Think of an Adaptive Card as a paper form. You hand it to the user, they fill in the boxes, hand it back, and your code processes it.

The spec lives at <https://adaptivecards.io>. Designer UI: <https://adaptivecards.io/designer>.

A minimal card:

```json
{
  "type": "AdaptiveCard",
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "version": "1.5",
  "body": [
    { "type": "TextBlock", "size": "Medium", "weight": "Bolder", "text": "Hello!" },
    { "type": "TextBlock", "text": "This is an Adaptive Card." }
  ],
  "actions": [
    { "type": "Action.OpenUrl", "title": "Learn more", "url": "https://adaptivecards.io" }
  ]
}
```

---

## 2️⃣ Sending a card from Python

```python
from microsoft_agents.activity import Activity, ActivityTypes, Attachment

ADAPTIVE_CARD_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"

card_json = { ... }   # your dict

attachment = Attachment(
    content_type=ADAPTIVE_CARD_CONTENT_TYPE,
    content=card_json,
)

await context.send_activity(Activity(
    type=ActivityTypes.MESSAGE,
    attachments=[attachment],
))
```

That's the whole pattern. Pack the dict into an `Attachment` with the magic content type, attach it to an `Activity`, send.

---

## 3️⃣ The 7 elements you'll use most

| Element | What it is |
|---|---|
| `TextBlock` | Static text (with size, weight, color, wrap) |
| `Input.Text` | Single- or multi-line text box |
| `Input.Number` | Numeric input |
| `Input.Date` | Date picker |
| `Input.ChoiceSet` | Dropdown / radio / checkbox list |
| `Action.Submit` | Sends form data back to your agent |
| `Action.OpenUrl` | Opens a link in browser |

Each `Input.*` needs an `id` — that's the key in the dict you receive when the user submits.

---

## 4️⃣ Receiving a submitted card

When the user clicks `Action.Submit`, the channel sends a **message activity** with the submitted form data attached as `activity.value` (a dict).

```python
@AGENT_APP.activity("message")
async def on_message(context, state):
    if context.activity.value:   # ← form submission
        data = context.activity.value
        await context.send_activity(f"Thanks! You submitted: {data}")
        return
    # Otherwise it's plain text
    await context.send_activity(f"Echo: {context.activity.text}")
```

> ⚠️ In Teams, some card actions arrive as `invoke` activities, not `message`. The pattern above works for `Action.Submit` in standard cards. We cover Teams-specific invokes in Phase 7.

---

## 5️⃣ Real-world example: Leave-Request Approval

**Scenario**: An employee types `request leave`. The agent sends a card with:

- Reason (text)
- Start date / End date
- Type (Vacation / Sick / Personal — dropdown)
- Submit button

When the employee submits, the agent stores the request, sends a confirmation card, and replies with the request ID.

### Card design (saved in [code/leave_request_agent/cards/leave_request.py](code/leave_request_agent/cards/leave_request.py))

```python
def build_leave_request_card() -> dict:
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


def build_confirmation_card(request_id: str, data: dict) -> dict:
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
```

### The agent ([code/leave_request_agent/app.py](code/leave_request_agent/app.py))

```python
"""Leave-Request Approval Agent — Phase 4 example."""
from __future__ import annotations
import uuid, logging

from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from microsoft_agents.activity import Activity, ActivityTypes, Attachment
from start_server import start_server
from cards.leave_request import build_leave_request_card, build_confirmation_card

ADAPTIVE_CARD = "application/vnd.microsoft.card.adaptive"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("leave")

AGENT_APP = AgentApplication(storage=MemoryStorage())


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context, state):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity("Type `request leave` to open the leave form.")


@AGENT_APP.message("request leave")
async def show_form(context, state):
    card = build_leave_request_card()
    await context.send_activity(Activity(
        type=ActivityTypes.MESSAGE,
        attachments=[Attachment(content_type=ADAPTIVE_CARD, content=card)],
    ))


@AGENT_APP.activity("message")
async def on_any(context, state):
    # 1. Form submission?
    if context.activity.value:
        data = dict(context.activity.value)
        if data.get("action") == "submit_leave":
            req_id = f"LR-{uuid.uuid4().hex[:6].upper()}"
            # Persist in conversation state for demo. In prod write to DB.
            requests = state.conversation.get("requests", [])
            requests.append({"id": req_id, **data})
            state.conversation["requests"] = requests
            log.info(f"Saved leave request {req_id}: {data}")
            confirm = build_confirmation_card(req_id, data)
            await context.send_activity(Activity(
                type=ActivityTypes.MESSAGE,
                attachments=[Attachment(content_type=ADAPTIVE_CARD, content=confirm)],
            ))
            return
    # 2. Plain text fallback
    await context.send_activity("Type `request leave` to start, or `list` to see your requests.")


@AGENT_APP.message("list")
async def list_requests(context, state):
    requests = state.conversation.get("requests", [])
    if not requests:
        await context.send_activity("No requests yet.")
        return
    bullets = "\n".join(f"- **{r['id']}** {r['leave_type']} {r['start']}→{r['end']}" for r in requests)
    await context.send_activity(f"Your requests:\n{bullets}")


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

---

## 6️⃣ Designing cards visually

The fastest way to design a new card:

1. Open <https://adaptivecards.io/designer>.
2. Drag and drop elements.
3. Copy the JSON.
4. Paste into a Python `dict` (or load from a `.json` file).

### Loading a card from a JSON file

```python
import json, pathlib

def load_card(name: str) -> dict:
    path = pathlib.Path(__file__).parent / "cards" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))
```

This separates content (JSON) from logic (Python). Recommended for non-trivial cards.

---

## 7️⃣ Card templating (`${var}`)

Adaptive Cards support a templating language using `${...}`. Render with the `adaptivecards-templating` package, or do simple substitution in Python:

```python
def render(template: dict, data: dict) -> dict:
    import json, string
    s = json.dumps(template)
    return json.loads(string.Template(s).substitute(data))

card = render(template, {"name": "Alice", "items": 3})
```

For complex cards use `pip install adaptive-cards-py` and its templating API.

---

## ✅ Phase 4 checklist

- [ ] You sent at least one card from your agent.
- [ ] You read `context.activity.value` when a user submitted a card.
- [ ] You understand the `Action.Submit.data` field is for routing on the server side.
- [ ] Your Leave-Request Agent works end-to-end.
- [ ] You completed [exercises.md](exercises.md).

Next → [Phase 5 — LLM Integration](../Phase5_LLM_Integration/README.md)
