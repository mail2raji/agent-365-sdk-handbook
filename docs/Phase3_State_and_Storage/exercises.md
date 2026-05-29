# 🧩 Phase 3 — Exercises

## Exercise 1 — Pick the scope

For each item, choose the right scope: **conversation**, **user**, or **temp**.

1. The user's preferred language.
2. The current page of a paginated list the user is browsing right now.
3. A temporary parsed date string used twice in the same turn.

<details><summary>Answer</summary>

1. `user` — survives across all the user's conversations.
2. `conversation` — relevant only inside this chat.
3. `temp` — only this turn.

</details>

---

## Exercise 2 — Default values

What's wrong with this line?

```python
cart = state.conversation["cart"]
```

<details><summary>Answer</summary>

If `cart` was never set, this raises `KeyError`. Use `.get()` with a default: `state.conversation.get("cart", [])`.

</details>

---

## Exercise 3 — Counter

Add a "ping" handler that increments a counter in conversation state and replies with the current count.

<details><summary>Answer</summary>

```python
@AGENT_APP.message("ping")
async def ping(context, state):
    count = state.conversation.get("ping_count", 0) + 1
    state.conversation["ping_count"] = count
    await context.send_activity(f"pong #{count}")
```

</details>

---

## Exercise 4 — Per-user nickname

Let users set a nickname with `nick <name>` (USER scope) and greet them with it on every `hi`.

<details><summary>Answer</summary>

```python
import re

NICK_RE = re.compile(r"^nick\s+(.+)$", re.IGNORECASE)

@AGENT_APP.message(NICK_RE)
async def set_nick(context, state):
    nick = NICK_RE.match(context.activity.text).group(1).strip()
    state.user["nick"] = nick
    await context.send_activity(f"Nickname saved as {nick}.")

@AGENT_APP.message("hi")
async def hi(context, state):
    nick = state.user.get("nick", "friend")
    await context.send_activity(f"Hi {nick}!")
```

</details>

---

## Exercise 5 — Save explicitly

When does `state.save(context)` definitely save state to the backend?

<details><summary>Answer</summary>

Immediately when called. It's safe to call multiple times. AgentApplication also calls it automatically at the end of a clean turn — but if your handler raises, you'd lose changes unless you saved before the exception.

</details>

---

## Exercise 6 — Quantities

Modify the cart to track quantities, e.g. `add apple` twice should show `apple x2`.

<details><summary>Answer</summary>

Use a dict instead of a list:

```python
def get_cart(state): return state.conversation.get("cart", {})  # dict[str,int]
def set_cart(state, cart): state.conversation["cart"] = cart

@AGENT_APP.message(ADD_RE)
async def add(context, state):
    item = ADD_RE.match(context.activity.text).group(1).strip()
    cart = get_cart(state)
    cart[item] = cart.get(item, 0) + 1
    set_cart(state, cart)
    await context.send_activity(f"✅ {item} x{cart[item]}")
```

</details>

---

## Exercise 7 — Total per item

Update `total` to use $1 × quantity for the dict version.

<details><summary>Answer</summary>

```python
@AGENT_APP.message("total")
async def total(context, state):
    cart = get_cart(state)
    n = sum(cart.values())
    await context.send_activity(f"💰 ${n}.00 ({n} item(s))")
```

</details>

---

## Exercise 8 — Persistent storage swap

What's the *only* code change required to migrate the cart agent to Azure Blob storage?

<details><summary>Answer</summary>

Replace the storage construction:

```python
from microsoft_agents.storage.blob import BlobStorage
storage = BlobStorage(connection_string=os.environ["AZURE_STORAGE_CONN"],
                      container_name="cart-state")
AGENT_APP = AgentApplication(storage=storage)
```

Everything else stays the same.

</details>

---

## Exercise 9 — Multi-instance gotcha

If you deploy two replicas of your agent behind a load balancer using `MemoryStorage`, what bug appears?

<details><summary>Answer</summary>

Replica A sees the user's cart, replica B doesn't. Every other request "loses" the cart. Fix: switch to a shared backend (Blob, Cosmos, Redis).

</details>

---

## Exercise 10 — Reset everything

Add a `reset all` command that clears **both** conversation and user state for the current caller.

<details><summary>Answer</summary>

```python
@AGENT_APP.message("reset all")
async def reset_all(context, state):
    state.conversation.clear()
    state.user.clear()
    await context.send_activity("All your saved data has been cleared.")
```

</details>

---

## Exercise 11 — Inspecting state

Add a debug command `show state` that dumps `state.conversation` and `state.user` as JSON.

<details><summary>Answer</summary>

```python
import json

@AGENT_APP.message("show state")
async def show_state(context, state):
    payload = {
        "conversation": dict(state.conversation),
        "user": dict(state.user),
    }
    await context.send_activity(f"```json\n{json.dumps(payload, indent=2)}\n```")
```

</details>

---

## Exercise 12 — Temp scope use

Why might you put a parsed JSON object in `state.temp` instead of recomputing it inside three handlers?

<details><summary>Answer</summary>

Performance and DRY. Compute once in a `before_turn` middleware, read three times. `state.temp` is wiped at end of turn, so no persistence cost.

</details>

---

## Exercise 13 — Last message memory

Store the previous user message in conversation state and respond to "what did I just say?" with it.

<details><summary>Answer</summary>

```python
@AGENT_APP.message("what did I just say?")
async def recall(context, state):
    last = state.conversation.get("last", "<nothing>")
    await context.send_activity(f"You said: {last}")

@AGENT_APP.activity("message")
async def remember(context, state):
    # Save the previous before computing reply
    # (register this LAST so other handlers run first)
    state.conversation["last"] = context.activity.text
```

</details>

---

## Exercise 14 — Bonus: limit cart size

Refuse to add a 6th item.

<details><summary>Answer</summary>

```python
@AGENT_APP.message(ADD_RE)
async def add(context, state):
    item = ADD_RE.match(context.activity.text).group(1).strip()
    cart = get_cart(state)
    if len(cart) >= 5:
        await context.send_activity("🛑 Cart is full (5 items max).")
        return
    cart.append(item)
    set_cart(state, cart)
    await context.send_activity(f"✅ {item} added.")
```

</details>

---

## Exercise 15 — Bonus: per-user pinned items

Let users `pin <item>` to their **user** profile so they appear in **every** new cart.

<details><summary>Answer</summary>

```python
PIN_RE = re.compile(r"^pin\s+(.+)$", re.IGNORECASE)

@AGENT_APP.message(PIN_RE)
async def pin(context, state):
    item = PIN_RE.match(context.activity.text).group(1).strip()
    pins = state.user.get("pinned", [])
    if item not in pins:
        pins.append(item)
        state.user["pinned"] = pins
    await context.send_activity(f"📌 Pinned {item}.")

# When a new conversation starts, prepopulate cart from pins:
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context, state):
    pins = state.user.get("pinned", [])
    if pins:
        state.conversation["cart"] = list(pins)
        await context.send_activity(f"Loaded {len(pins)} pinned item(s) into your cart.")
```

</details>

---

✅ Next → **[Phase 4 — Adaptive Cards](../Phase4_Rich_Messaging/README.md)**.
