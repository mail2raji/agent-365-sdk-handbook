# 🧩 Phase 4 — Exercises

## Exercise 1 — Magic content type

What is the content type string for an Adaptive Card attachment?

<details><summary>Answer</summary>

`application/vnd.microsoft.card.adaptive`

</details>

---

## Exercise 2 — Where does the form data arrive?

When a user clicks `Action.Submit`, where in the activity do you read the form fields?

<details><summary>Answer</summary>

In `context.activity.value` (a dict whose keys match the `id` of each `Input.*` plus whatever you put in `Action.Submit.data`).

</details>

---

## Exercise 3 — Add a checkbox

Add a "Notify my manager?" checkbox to the leave-request card.

<details><summary>Answer</summary>

```python
{
  "type": "Input.Toggle",
  "id": "notify_manager",
  "title": "Notify my manager?",
  "value": "true",
  "valueOn": "true",
  "valueOff": "false"
}
```

</details>

---

## Exercise 4 — Validate dates server-side

In `on_any`, refuse the submission if `end < start`.

<details><summary>Answer</summary>

```python
if data["end"] < data["start"]:
    await context.send_activity("⚠️ End date must be on or after start date.")
    return
```

(Date strings from `Input.Date` are ISO 8601 `YYYY-MM-DD`, so string comparison works.)

</details>

---

## Exercise 5 — Open URL action

Add an `Action.OpenUrl` to the leave card that opens the company HR portal.

<details><summary>Answer</summary>

```python
"actions": [
    {"type": "Action.Submit", "title": "Submit", "data": {"action": "submit_leave"}},
    {"type": "Action.OpenUrl", "title": "HR Portal", "url": "https://hr.contoso.com"},
]
```

</details>

---

## Exercise 6 — Routing multiple cards

You have two cards: one for *leave* and one for *expense*. How do you tell them apart on submit?

<details><summary>Answer</summary>

Each `Action.Submit` has a `data` payload — put a unique `action` value:

```python
{"action": "submit_leave"}
{"action": "submit_expense"}
```

In your handler:

```python
if data["action"] == "submit_leave": ...
elif data["action"] == "submit_expense": ...
```

</details>

---

## Exercise 7 — Card from JSON file

Refactor `build_leave_request_card` to load from `cards/leave_request.json` instead of a Python dict.

<details><summary>Answer</summary>

```python
import json, pathlib

def load_card(name: str) -> dict:
    p = pathlib.Path(__file__).parent.parent / "cards" / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8"))

# Use:
card = load_card("leave_request")
```

</details>

---

## Exercise 8 — Required fields

How do you mark an `Input.Text` as required and show a custom error?

<details><summary>Answer</summary>

```python
{"type": "Input.Text", "id": "reason", "label": "Reason",
 "isRequired": True, "errorMessage": "Reason is required."}
```

</details>

---

## Exercise 9 — FactSet

What's a `FactSet` good for and what's its JSON shape?

<details><summary>Answer</summary>

A `FactSet` shows label/value pairs in a clean two-column layout — great for confirmations.

```python
{"type": "FactSet", "facts": [
    {"title": "Status", "value": "Submitted"},
    {"title": "ID", "value": "LR-ABC123"},
]}
```

</details>

---

## Exercise 10 — Send card + text together

Send a card AND a follow-up text message in the same handler.

<details><summary>Answer</summary>

Call `send_activity` twice:

```python
await context.send_activity(Activity(type="message", attachments=[Attachment(...)]))
await context.send_activity("Anything else?")
```

</details>

---

## Exercise 11 — Bonus: yes/no card

Build a quick yes/no card using two `Action.Submit` buttons.

<details><summary>Answer</summary>

```python
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [{"type": "TextBlock", "text": "Are you sure?"}],
  "actions": [
    {"type": "Action.Submit", "title": "Yes", "data": {"action": "confirm", "value": True}},
    {"type": "Action.Submit", "title": "No",  "data": {"action": "confirm", "value": False}},
  ],
}
```

</details>

---

## Exercise 12 — Bonus: pre-fill values

Send the card with the user's last reason already typed in.

<details><summary>Answer</summary>

Set the `value` property on `Input.Text`:

```python
{"type": "Input.Text", "id": "reason", "label": "Reason",
 "value": state.conversation.get("last_reason", "")}
```

</details>

---

## Exercise 13 — Bonus: image

Add a small logo at the top of the confirmation card.

<details><summary>Answer</summary>

```python
{"type": "Image", "url": "https://adaptivecards.io/content/cats/1.png",
 "size": "Small", "altText": "Logo"}
```

</details>

---

## Exercise 14 — Bonus: ColumnSet for layout

Split the form into two columns (start date left, end date right).

<details><summary>Answer</summary>

```python
{
  "type": "ColumnSet",
  "columns": [
    {"type": "Column", "width": "stretch", "items": [
        {"type": "Input.Date", "id": "start", "label": "Start"}
    ]},
    {"type": "Column", "width": "stretch", "items": [
        {"type": "Input.Date", "id": "end", "label": "End"}
    ]},
  ]
}
```

</details>

---

## Exercise 15 — Bonus: card version

The current card uses `"version": "1.5"`. What happens in a channel that only supports 1.3?

<details><summary>Answer</summary>

The channel renders what it can. Newer features (like input labels) may show as plain text or be skipped. To be safe, target the lowest version every channel supports (1.3 is broadly safe; 1.5 is Teams + modern Outlook).

</details>

---

✅ Next → **[Phase 5 — LLM Integration](../Phase5_LLM_Integration/README.md)**.
