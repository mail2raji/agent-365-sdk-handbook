# 🧩 Phase 2 — Exercises

## Exercise 1 — Decorator picker

Which decorator fires when a **new user joins**?

<details><summary>Answer</summary>

`@AGENT_APP.conversation_update("membersAdded")`

</details>

---

## Exercise 2 — Greet the user by name

Modify `welcome` so it says `Welcome, <name>!` instead of just the menu.

<details><summary>Answer</summary>

```python
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context, _state):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(f"Welcome, {m.name or 'friend'}!\n\n{MENU}")
```

</details>

---

## Exercise 3 — Order matters (again)

If you put `@AGENT_APP.activity("message")` **above** `@AGENT_APP.message("/help")`, what happens?

<details><summary>Answer</summary>

The catch-all eats the "/help" message and your `on_help` handler never runs. Always register specific routes first.

</details>

---

## Exercise 4 — Add a new department: Travel

Route messages containing "flight", "hotel", or "trip" to a new Travel handler.

<details><summary>Answer</summary>

```python
@AGENT_APP.message(["flight", "hotel", "trip"])
async def route_travel(context, _state):
    await context.send_activity("✈️ Connecting you to Travel desk.")
```

Put it **above** the catch-all `default` handler.

</details>

---

## Exercise 5 — Regex anchoring

Why does the IT regex use `\b...\b` instead of just the keywords?

<details><summary>Answer</summary>

`\b` is a **word boundary**. Without it, "password" would also match inside "passwordless" or "newpassword123". `\b` ensures we match the whole word.

</details>

---

## Exercise 6 — Case sensitivity

By default, are `@AGENT_APP.message("Hello")` matches **case-sensitive**?

<details><summary>Answer</summary>

Exact string matching in `@message(...)` is case-**insensitive** for plain strings. For regex you must pass `re.IGNORECASE` explicitly: `re.compile(r"...", re.IGNORECASE)`.

</details>

---

## Exercise 7 — Conversation removed

Add a handler that logs when a user **leaves** the conversation.

<details><summary>Answer</summary>

```python
@AGENT_APP.conversation_update("membersRemoved")
async def on_leave(context, _state):
    for m in context.activity.members_removed or []:
        log.info(f"{m.name or m.id} left the conversation.")
```

</details>

---

## Exercise 8 — Inspect every activity

Add a debug handler that logs the type of every activity (without consuming it).

<details><summary>Answer</summary>

```python
@AGENT_APP.before_turn      # runs before any other handler
async def trace(context, _state):
    log.info(f"Got activity: {context.activity.type}")
```

> Note: if `before_turn` is unavailable in your SDK version, register a normal `@activity(...)` for each type or use middleware. The `before_turn` hook in `AgentApplication` is the standard place for tracing.

</details>

---

## Exercise 9 — Distinguish channels

Reply differently if the message came from Teams vs. web chat.

<details><summary>Answer</summary>

```python
@AGENT_APP.activity("message")
async def default(context, _state):
    if context.activity.channel_id == "msteams":
        await context.send_activity("👋 Hi Teams user!")
    elif context.activity.channel_id == "webchat":
        await context.send_activity("👋 Hi web visitor!")
    else:
        await context.send_activity("👋 Hi!")
```

</details>

---

## Exercise 10 — Markdown formatting

Send a reply that contains a **bold** word and a *italic* word.

<details><summary>Answer</summary>

```python
from microsoft_agents.activity import Activity, ActivityTypes

await context.send_activity(Activity(
    type=ActivityTypes.MESSAGE,
    text="This is **bold** and this is *italic*.",
    text_format="markdown",
))
```

Most channels render markdown by default, so a plain string usually works too.

</details>

---

## Exercise 11 — Mentions in Teams

In Teams, when a user `@`mentions the bot, where can you find the mention metadata?

<details><summary>Answer</summary>

In `context.activity.entities`. Each entity has a `type` like `"mention"`. You can filter:

```python
mentions = [e for e in (context.activity.entities or []) if getattr(e, "type", "") == "mention"]
```

</details>

---

## Exercise 12 — Multi-turn pattern

Why is a stateless handler ("I don't remember the last message") a bad fit for a follow-up like *"What was my previous question?"*?

<details><summary>Answer</summary>

Because each turn is a fresh function call — local variables are wiped between turns. To remember anything you need **state** (Phase 3) tied to `conversation.id` or `user.id`.

</details>

---

## Exercise 13 — Route metric

Increment a global counter every time the IT route fires (for logging purposes).

<details><summary>Answer</summary>

```python
IT_COUNT = 0

@AGENT_APP.message(IT_REGEX)
async def route_it(context, _state):
    global IT_COUNT
    IT_COUNT += 1
    log.info(f"IT routes: {IT_COUNT}")
    await context.send_activity("🔐 Connecting you to IT.")
```

> Note: this only works on one process. For multi-instance deployments use a real metric backend (Phase 9).

</details>

---

## Exercise 14 — Bonus: list **and** regex

Route the words "bye", "goodbye", or anything matching `^cya.*$` to a farewell handler.

<details><summary>Answer</summary>

```python
import re

@AGENT_APP.message(["bye", "goodbye", re.compile(r"^cya.*$", re.IGNORECASE)])
async def farewell(context, _state):
    await context.send_activity("👋 Bye! Come back anytime.")
```

</details>

---

## Exercise 15 — Bonus: time-of-day greeting

Greet users with "Good morning/afternoon/evening" based on the **server's** local hour.

<details><summary>Answer</summary>

```python
from datetime import datetime

@AGENT_APP.conversation_update("membersAdded")
async def welcome(context, _state):
    hr = datetime.now().hour
    when = "morning" if hr < 12 else "afternoon" if hr < 18 else "evening"
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(f"Good {when}, {m.name or 'friend'}!")
```

</details>

---

✅ Next → **[Phase 3 — State & Storage](../Phase3_State_and_Storage/README.md)**.
