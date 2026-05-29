# 🧩 Phase 1 — Exercises

## Exercise 1 — Activity types

Name three values that can appear in `activity.type`.

<details><summary>Answer</summary>

Common types: `message`, `conversationUpdate`, `event`, `invoke`, `typing`, `messageReaction`, `endOfConversation`.
For this curriculum the three most important are **`message`**, **`conversationUpdate`**, **`event`**.

</details>

---

## Exercise 2 — Decorator vocab

What decorator would you use to catch only the exact text **"reset"**?

<details><summary>Answer</summary>

```python
@AGENT_APP.message("reset")
async def on_reset(context, state):
    await context.send_activity("State reset.")
```

</details>

---

## Exercise 3 — Decorator vocab 2

What decorator catches **any** message, regardless of text?

<details><summary>Answer</summary>

```python
@AGENT_APP.activity("message")
async def on_any_message(context, state):
    ...
```

</details>

---

## Exercise 4 — Order matters

In `app.py` you have:

```python
@AGENT_APP.activity("message")
async def catch_all(...): ...

@AGENT_APP.message("/help")
async def on_help(...): ...
```

A user types `/help`. What's printed by `on_help`?

<details><summary>Answer</summary>

Nothing — `catch_all` is registered first and a broader route swallows the message before `on_help` gets a chance. **Put specific routes first.**

</details>

---

## Exercise 5 — Reply with multiple messages

Modify `on_help` to send **two** consecutive messages.

<details><summary>Answer</summary>

```python
@AGENT_APP.message("/help")
async def on_help(context, state):
    await context.send_activity("Here's the help:")
    await context.send_activity("Type anything and I'll echo it.")
```

</details>

---

## Exercise 6 — Read the user's name

Inside a message handler, how do you get the **sender's display name**?

<details><summary>Answer</summary>

```python
name = context.activity.from_property.name
```

(`from` is a Python reserved word, so the property is renamed to `from_property`.)

</details>

---

## Exercise 7 — Conversation ID

Where can you find the unique ID of the current conversation?

<details><summary>Answer</summary>

```python
conv_id = context.activity.conversation.id
```

</details>

---

## Exercise 8 — Catch a different activity type

Add a handler that runs when the channel reports the user is typing.

<details><summary>Answer</summary>

```python
@AGENT_APP.activity("typing")
async def on_typing(context, state):
    # Most channels send typing indicators — silently log them
    print(f"User {context.activity.from_property.id} is typing…")
```

</details>

---

## Exercise 9 — Echo only the last 50 chars

Limit the echo to the last 50 characters of the incoming message.

<details><summary>Answer</summary>

```python
@AGENT_APP.activity("message")
async def on_any_message(context, state):
    text = (context.activity.text or "")[-50:]
    await context.send_activity(f"Echo: {text}")
```

</details>

---

## Exercise 10 — Regex matching

Match any message that **starts with** `order ` followed by digits, e.g. `order 12345`.

<details><summary>Answer</summary>

```python
import re

@AGENT_APP.message(re.compile(r"^order\s+\d+$", re.IGNORECASE))
async def on_order(context, state):
    await context.send_activity("Looking up your order…")
```

</details>

---

## Exercise 11 — Why `async`?

Why must every handler be `async def` and not `def`?

<details><summary>Answer</summary>

The SDK and the underlying `aiohttp` server are **asynchronous** — they use `asyncio` to handle many requests concurrently without threads. A blocking `def` handler would freeze the whole event loop.

</details>

---

## Exercise 12 — `send_activity` shortcuts

What's the difference between:

```python
await context.send_activity("Hi")
await context.send_activity(Activity(type="message", text="Hi"))
```

<details><summary>Answer</summary>

They're equivalent. Passing a string is a shortcut — the SDK wraps it in `Activity(type="message", text=...)` automatically.

</details>

---

## Exercise 13 — Where does the port come from?

In `start_server.py` we used:

```python
port = int(os.environ.get("PORT", 3978))
```

What does this expression do?

<details><summary>Answer</summary>

It reads the environment variable `PORT`. If unset, defaults to `3978`. `int(...)` converts the string to an integer. This lets Azure App Service inject `PORT` at runtime in Phase 9.

</details>

---

## Exercise 14 — Bonus: Build a "rude" agent

Make an agent that **rejects** any message containing the word "please" (politely 😄).

<details><summary>Answer</summary>

```python
@AGENT_APP.activity("message")
async def on_message(context, state):
    text = (context.activity.text or "").lower()
    if "please" in text:
        await context.send_activity("Ugh, manners. I'll ignore that.")
        return
    await context.send_activity(f"Echo: {context.activity.text}")
```

</details>

---

## Exercise 15 — Bonus: Read the channel

Echo back **which channel** sent the message (`msteams`, `webchat`, `emulator`, …).

<details><summary>Answer</summary>

```python
@AGENT_APP.activity("message")
async def on_message(context, state):
    ch = context.activity.channel_id
    await context.send_activity(f"You messaged me from {ch}. You said: {context.activity.text}")
```

</details>

---

✅ Next → **[Phase 2 — Activities & Handlers](../Phase2_Activities_and_Handlers/README.md)**.
