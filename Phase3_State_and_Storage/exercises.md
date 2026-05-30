# 🧪 Phase 3 — Hands-On Lab: Shopping-Cart Agent with Real Memory

> A step-by-step lab. By the end you'll have an agent that **remembers** what's in your shopping cart even across multiple messages — and remembers your language preference forever.

---

## 🎯 What you'll build today

A shopping-cart agent that:

1. Lets you `add bread`, `add milk`, etc. — items stick around across turns.
2. Shows your cart with `cart`.
3. Removes items with `remove bread`.
4. Empties the cart with `clear`.
5. Calculates a fake total with `total`.
6. Lets you set your **personal** language with `lang en|de|fr` — and greets you in that language forever.
7. Survives a server restart (after Lab 5, using **persistent file storage**).

> 👶 Think of an agent without state as a goldfish with a 1-second memory: every message is a fresh start. We're going to give it a notebook so it can remember what you said before.

⏱️ **About 75 minutes**.

---

## ✅ Before you start

- [ ] Phase 2 finished — helpdesk_router worked.
- [ ] Terminal prompt starts with **`(.venv)`**.
- [ ] You have the `Send-Msg` helper from Phase 2 still loaded in your test terminal (or be ready to paste it again).

---

## 🗺️ Today's roadmap

```
Lab 1 → Prove an agent forgets without state
Lab 2 → Add MemoryStorage and watch the cart survive multiple turns
Lab 3 → Show the difference between conversation- and user-scope state
Lab 4 → Multi-user test — Alice's cart shouldn't appear in Bob's chat
Lab 5 → Swap MemoryStorage for FileStorage so the cart survives restarts
```

---

## Lab 1 — Prove the goldfish problem (~10 min)

**You will:** build an agent that *tries* to remember a cart using a plain Python variable, watch it fail, and understand why.

### Step 1.1 — Make a lab folder

```powershell
cd Phase3_State_and_Storage
mkdir -Force lab_cart
cd lab_cart
```

### Step 1.2 — Copy `start_server.py` from a prior phase

```powershell
Copy-Item ..\code\shopping_cart_agent\start_server.py .
```

### Step 1.3 — Make `app_v1.py` (the broken version)

```powershell
New-Item app_v1.py -ItemType File
code app_v1.py
```

Paste this:

```python
"""app_v1.py — broken on purpose: uses a normal variable instead of state."""
from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from start_server import start_server
import re

AGENT_APP = AgentApplication(storage=MemoryStorage())

# 🐛 BROKEN: a single global cart for the whole process
cart: list[str] = []


@AGENT_APP.message(re.compile(r"^add\s+(.+)$", re.IGNORECASE))
async def add_item(context: TurnContext, state: TurnState):
    item = re.match(r"^add\s+(.+)$", context.activity.text, re.IGNORECASE).group(1).strip()
    cart.append(item)
    await context.send_activity(f"Added {item}. Cart has {len(cart)} item(s).")


@AGENT_APP.message("cart")
async def show_cart(context: TurnContext, state: TurnState):
    await context.send_activity(f"🛒 {cart or 'empty'}")


@AGENT_APP.activity("message")
async def help_(context, state):
    await context.send_activity("Try `add bread`, `add milk`, then `cart`.")


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

Save.

### Step 1.4 — Run it & check the cart

```powershell
python app_v1.py
```

In terminal 2:

```powershell
function Send-Msg {
    param([string]$Text, [string]$User="alice")
    $body = @{
        type="message"; text=$Text
        from=@{id=$User; name=$User}; recipient=@{id="bot"}
        conversation=@{id="c-$User"}; serviceUrl="http://localhost"
    } | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Uri http://localhost:3978/api/messages `
        -Method POST -ContentType "application/json" -Body $body
}

Send-Msg "add bread"   # ok
Send-Msg "add milk"    # ok
Send-Msg "cart"        # 🐛 see the bug
```

The cart appears to work — `bread` and `milk` are there. **But!**

### Step 1.5 — Show the multi-user bug

```powershell
Send-Msg "add fish" -User bob     # Bob adds fish
Send-Msg "cart"      -User alice  # Alice sees fish too!
```

Bob's fish appears in Alice's cart, because the variable is **shared across the whole process**. This is why we need *state*.

### Step 1.6 — Show the restart bug

Stop the agent in terminal 1 (`Ctrl+C`). Restart:

```powershell
python app_v1.py
```

```powershell
Send-Msg "cart"        # 🐛 empty — the cart didn't survive restart
```

**What just happened?** You proved that plain Python variables are like a goldfish — they remember nothing for long. Two big problems showed up: (1) everyone shares the same brain, (2) the brain resets every time the agent restarts. The whole point of "state" is to fix both bugs.

### ✅ Checkpoint 1
You've seen **two bugs** of using plain variables: (a) all users share one cart, (b) restart wipes everything.

Stop the agent (`Ctrl+C`).

---

## Lab 2 — Conversation-scope state (~15 min)

**You will:** rewrite the cart using `state.conversation` so each conversation gets its own cart.

### Step 2.1 — Create `app_v2.py`

```powershell
Copy-Item app_v1.py app_v2.py
code app_v2.py
```

Replace the contents with:

```python
"""app_v2.py — cart stored in conversation-scope state."""
from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from start_server import start_server
import re

AGENT_APP = AgentApplication(storage=MemoryStorage())


def get_cart(state: TurnState) -> list[str]:
    return state.conversation.get("cart", [])

def set_cart(state: TurnState, cart: list[str]) -> None:
    state.conversation["cart"] = cart


@AGENT_APP.message(re.compile(r"^add\s+(.+)$", re.IGNORECASE))
async def add_item(context: TurnContext, state: TurnState):
    item = re.match(r"^add\s+(.+)$", context.activity.text, re.IGNORECASE).group(1).strip()
    cart = get_cart(state)
    cart.append(item)
    set_cart(state, cart)
    await context.send_activity(f"Added {item}. Cart has {len(cart)} item(s).")


@AGENT_APP.message("cart")
async def show_cart(context: TurnContext, state: TurnState):
    cart = get_cart(state)
    await context.send_activity(f"🛒 {cart or 'empty'}")


@AGENT_APP.message("clear")
async def clear_cart(context: TurnContext, state: TurnState):
    set_cart(state, [])
    await context.send_activity("Cart cleared.")


@AGENT_APP.activity("message")
async def help_(context, state):
    await context.send_activity("Try `add bread`, `cart`, `clear`.")


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

Save.

### Step 2.2 — Run & verify multi-user works

```powershell
python app_v2.py
```

```powershell
Send-Msg "add bread"  -User alice
Send-Msg "add fish"   -User bob
Send-Msg "cart"       -User alice    # → only ['bread']
Send-Msg "cart"       -User bob      # → only ['fish']
```

🎉 Now Alice and Bob have their **own** carts because each user has a different `conversation.id`.

### Step 2.3 — Decode `state.conversation`

- `state.conversation` is a **dict-like object** scoped to the conversation id.
- The SDK loads it at the start of every turn and saves it at the end.
- Each unique `conversation.id` in the incoming activity gets its own dict.

> 🧠 **The save-after-modify rule:** `MemoryStorage` is forgiving — it saves automatically. **Persistent** backends (FileStorage, Blob, Cosmos) only save when `AgentApplication` decides the turn was clean. To be safe, call `await state.save(context)` after big changes, especially inside `try/except`.

**What just happened?** You moved the cart from a shared global into `state.conversation` — a dict the SDK gives each conversation. Now every chat has its own private cart. Same code, but it works for thousands of users at once. This is the **first real win** from the M365 Agents SDK.

### ✅ Checkpoint 2
Two users, two carts. No cross-contamination. Stop the agent (`Ctrl+C`).

---

## Lab 3 — User-scope state (language preference) (~15 min)

**You will:** add a language preference that follows the user across all their conversations.

### Step 3.1 — Make `app_v3.py`

```powershell
Copy-Item app_v2.py app_v3.py
code app_v3.py
```

Add **before the `help_` handler**:

```python
GREETINGS = {"en": "Hello!", "de": "Hallo!", "fr": "Bonjour!"}

def get_lang(state: TurnState) -> str:
    return state.user.get("lang", "en")

def set_lang(state: TurnState, lang: str) -> None:
    state.user["lang"] = lang


@AGENT_APP.message(re.compile(r"^lang\s+(en|de|fr)$", re.IGNORECASE))
async def set_language(context: TurnContext, state: TurnState):
    lang = re.match(r"^lang\s+(\w+)$", context.activity.text, re.IGNORECASE).group(1).lower()
    set_lang(state, lang)
    await context.send_activity(f"Language saved as **{lang}** for your profile.")


@AGENT_APP.message(["hi", "hello", "hey"])
async def greet(context: TurnContext, state: TurnState):
    await context.send_activity(GREETINGS[get_lang(state)])
```

> ⚠️ Make sure these handlers come **before** the `help_` catch-all in the file (specific → general rule from Phase 2).

Save.

### Step 3.2 — Update `Send-Msg` to support multiple conversations per user

```powershell
function Send-Msg {
    param([string]$Text, [string]$User="alice", [string]$Conv="default")
    $body = @{
        type="message"; text=$Text
        from=@{id=$User; name=$User}; recipient=@{id="bot"}
        conversation=@{id="$User-$Conv"}; serviceUrl="http://localhost"
    } | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Uri http://localhost:3978/api/messages `
        -Method POST -ContentType "application/json" -Body $body
}
```

### Step 3.3 — Run & verify

```powershell
python app_v3.py
```

```powershell
# Alice sets language in conversation A
Send-Msg "lang de" -User alice -Conv chatA
Send-Msg "hi"      -User alice -Conv chatA     # → Hallo!

# Alice opens a NEW conversation B — but it's still Alice
Send-Msg "hi"      -User alice -Conv chatB     # → Hallo!  (👈 user-scope kept it)

# Bob is a different user
Send-Msg "hi"      -User bob   -Conv chatA     # → Hello!  (default, not Alice's)
```

🎉 Language is **user-scoped** — follows Alice across all her conversations, but doesn't leak to Bob.

**What just happened?** You learned the **two scopes** rule: `state.conversation` is per-chat (the cart), `state.user` is per-person (the language). Pick the right one based on what should leak across chats and what shouldn't. Mixing them up is the #1 state bug in real agents.

### ✅ Checkpoint 3
Alice gets `Hallo!` in any conversation; Bob gets `Hello!`. Stop the agent.

---

## Lab 4 — The save-after-modify trap (~10 min)

**You will:** force a crash mid-turn and see what happens to state.

### Step 4.1 — Add a buggy handler to `app_v3.py`

Insert this **before** `help_`:

```python
@AGENT_APP.message("boom")
async def boom(context: TurnContext, state: TurnState):
    cart = get_cart(state)
    cart.append("💥")
    set_cart(state, cart)
    # await state.save(context)        # try uncommenting in Step 4.4
    raise RuntimeError("Simulated crash before reply!")
```

Save.

### Step 4.2 — Run

```powershell
python app_v3.py
```

### Step 4.3 — Trigger it

```powershell
Send-Msg "add apple" -User alice
Send-Msg "cart"      -User alice      # → ['apple']
Send-Msg "boom"      -User alice      # → terminal 1 shows traceback
Send-Msg "cart"      -User alice      # → ???
```

With `MemoryStorage`, you'll **probably** still see `['apple']` because state was already in memory before the crash. **But** in production with Blob/Cosmos, the partial change (the `💥` we appended) may or may not have persisted, depending on whether the save happened. This is the **save-after-modify** problem.

### Step 4.4 — Fix it the "safe" way

Edit `boom` and **uncomment** the `await state.save(context)` line so it runs *before* the crash. Save & restart. Re-trigger.

Now the `💥` is definitely in the cart, because we saved before the raise.

> 🧠 **Lesson:** for important state changes, call `await state.save(context)` immediately after modifying, so the data survives even if your code crashes.

**What just happened?** You watched a crash and learned a fire-drill habit: when something **important** changes (a payment, a ticket, money), save **immediately** — don't trust the SDK to do it at the end of the turn. One missed save = one upset user.

### ✅ Checkpoint 4
You've seen a controlled crash and understood why explicit `state.save()` is sometimes necessary.

Remove the `boom` handler (it was just a demo). Stop the agent.

---

## Lab 5 — Persistent storage with `FileStorage` (~15 min)

**You will:** swap `MemoryStorage` for **`FileStorage`** so the cart survives a server restart. (For real production you'd use BlobStorage or CosmosDb — same idea, fancier backend.)

### Step 5.1 — Check if FileStorage exists in this SDK build

```powershell
python -c "from microsoft_agents.hosting.core.storage import FileStorage; print('OK')"
```

If that prints `OK`, you can use FileStorage. **If it says `ImportError`, this SDK build doesn't ship it** — skip to Step 5.4 for an alternative.

### Step 5.2 — Switch storage in `app_v3.py`

Open `app_v3.py`. Change the import and the storage line:

```python
from microsoft_agents.hosting.core import (
    AgentApplication, TurnContext, TurnState,
)
from microsoft_agents.hosting.core.storage import FileStorage   # ← new import

AGENT_APP = AgentApplication(storage=FileStorage(folder="./state"))
```

Save.

### Step 5.3 — Verify restart survival

```powershell
python app_v3.py
```

```powershell
Send-Msg "add bread" -User alice
Send-Msg "add milk"  -User alice
Send-Msg "cart"      -User alice     # → ['bread', 'milk']
```

Stop the agent (`Ctrl+C`). Restart:

```powershell
python app_v3.py
Send-Msg "cart"      -User alice     # → ['bread', 'milk']   ← survived!
```

Look in the folder:

```powershell
Get-ChildItem state
```

You'll see JSON files like `conversation_alice-default.json` containing your cart. That's where the state went.

### Step 5.4 — Alternative: tiny custom storage (only if FileStorage missing)

If your SDK build doesn't have FileStorage, create `simple_file_storage.py` in your lab folder:

```python
"""simple_file_storage.py — a 30-line file-backed Storage for demos."""
from __future__ import annotations
import json, os, asyncio
from typing import Any
from microsoft_agents.hosting.core import Storage


class SimpleFileStorage(Storage):
    def __init__(self, folder: str = "./state"):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)
        self._lock = asyncio.Lock()

    def _path(self, key: str) -> str:
        safe = key.replace("/", "_").replace("\\", "_")
        return os.path.join(self.folder, f"{safe}.json")

    async def read(self, keys: list[str]) -> dict[str, Any]:
        async with self._lock:
            out: dict[str, Any] = {}
            for k in keys:
                p = self._path(k)
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        out[k] = json.load(f)
            return out

    async def write(self, changes: dict[str, Any]) -> None:
        async with self._lock:
            for k, v in changes.items():
                with open(self._path(k), "w", encoding="utf-8") as f:
                    json.dump(v, f, indent=2, default=str)

    async def delete(self, keys: list[str]) -> None:
        async with self._lock:
            for k in keys:
                p = self._path(k)
                if os.path.exists(p):
                    os.remove(p)
```

In `app_v3.py`:

```python
from simple_file_storage import SimpleFileStorage
AGENT_APP = AgentApplication(storage=SimpleFileStorage(folder="./state"))
```

Re-run the same test as Step 5.3. Cart should survive a restart.

**What just happened?** You swapped the **storage backend** (RAM → disk) without changing a single line of business logic. That's the magic of the `Storage` abstraction — in production you'd swap again to `BlobStorage` or `CosmosDbStorage` and your handlers wouldn't notice.

### ✅ Checkpoint 5
Restart the agent — Alice's cart is still there.

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| Bob's items appear in Alice's cart | Both messages used the same `conversation.id`. | Make sure your test helper uses `conversation=@{id="$User-$Conv"}` (different ids per user). |
| Language persists for the wrong user | You stored it in `state.conversation` instead of `state.user`. | Use `state.user["lang"] = ...`. |
| `from_property` is `None` | The incoming JSON didn't include a `from`. | Add `from=@{id="u1"; name="Alice"}` to your test JSON. |
| Cart resets between turns even with `MemoryStorage` | You forgot `set_cart(state, cart)` after appending. | Always write back: `state.conversation["cart"] = cart`. |
| Files written to `state/` are empty | Storage handler raised before save. | Wrap risky logic in `try` and `await state.save(context)` first. |
| `ImportError: FileStorage` | Older SDK build. | Use the SimpleFileStorage class in Step 5.4. |

---

## 🎓 Self-check

1. **What are the 3 state scopes and what does each one live for?**

   <details><summary>Show answer</summary>

   - `state.conversation` — one conversation (a chat thread).
   - `state.user` — one user, across all their conversations.
   - `state.temp` — one turn only.
   </details>

2. **Why did Bob see Alice's items in Lab 1?**

   <details><summary>Show answer</summary>
   The cart was a global Python variable shared across the whole process — every user wrote to and read from the same list.
   </details>

3. **Where should "preferred language" live: conversation, user, or temp scope?**

   <details><summary>Show answer</summary>
   `user` scope. It's a personal preference that should follow the user across *all* their conversations.
   </details>

4. **What does the save-after-modify rule say?**

   <details><summary>Show answer</summary>
   `MemoryStorage` saves automatically, but persistent backends (File, Blob, Cosmos) only save at the end of a clean turn. If your handler crashes, state may be lost. Call `await state.save(context)` explicitly after important changes.
   </details>

5. **For production, which storage backend would you pick and why?**

   <details><summary>Show answer</summary>
   For most cases: **Azure Blob Storage** — cheap, scales well. For high-traffic or low-latency reads, **Cosmos DB**. **Never** ship MemoryStorage in production — restart wipes everything.
   </details>

---

## 🚀 Bonus tasks

1. **Make `total` smarter** — store a `prices` dict in `state.conversation` with `{item: float}` and compute a real total.
2. **Add `last_added`** — store the most recent item in `state.temp` (just for the turn) and show it in the reply.
3. **Throw away test data** — add a `wipe me` command that deletes the user's state file (FileStorage version).
4. **Try BlobStorage** — install `microsoft-agents-storage-blob`, point it at an Azurite container, swap `FileStorage` for `BlobStorage`. Same code shape — only the constructor changes.

---

## 🏁 You're done!

You now know:

- Why agents need state (the goldfish problem).
- The three scopes: `conversation`, `user`, `temp`.
- How to use `MemoryStorage` (dev) and `FileStorage` (durable).
- The save-after-modify rule.

Next → [Phase 4 — Rich Messaging with Adaptive Cards](../Phase4_Rich_Messaging/README.md)
