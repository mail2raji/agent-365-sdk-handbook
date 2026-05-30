# 🧪 Phase 2 — Hands-On Lab: Build a Help-Desk Router

> A step-by-step lab. By the end you'll have a working chat agent that routes employee questions to **IT**, **HR**, or **Finance** based on what they type.

---

## 🎯 What you'll build today

A small but realistic agent called **`helpdesk_router`**:

1. Greets every new user with a menu of options.
2. Routes "password" / "locked out" / "MFA" questions to **IT** (using a regex).
3. Routes "payslip" / "leave balance" questions to **HR** (using a keyword list).
4. Routes "expense" / "invoice" questions to **Finance**.
5. Shows the menu again if it doesn't recognise the text.
6. Logs every routing decision to the terminal.

You'll also learn the **most important rule** of agent routing: **specific handlers must be registered before catch-alls.**

> 👶 Imagine the agent is a hotel concierge at a desk. When you walk up and say "I lost my key", the concierge sends you to housekeeping. Say "expense report", and they send you to finance. Say nothing useful? They hand you a menu. Same idea — we just code it in Python.

⏱️ **About 60 minutes** if you take your time.

---

## ✅ Before you start

- [ ] Phase 1 finished — you can run the echo agent.
- [ ] Terminal prompt starts with **`(.venv)`**.
- [ ] You remember the PowerShell `Invoke-RestMethod` trick from Phase 1 (we'll reuse it).

---

## 🗺️ Today's roadmap

```
Lab 1 → Open the prebuilt helpdesk_router and decode it
Lab 2 → Run it and test all 4 routes from PowerShell
Lab 3 → Break the routing order on purpose (learn the #1 routing rule)
Lab 4 → Add a 4th team: "Travel"
Lab 5 → Add lifecycle handlers (membersRemoved & typing)
```

---

## Lab 1 — Open the helpdesk_router and decode it (~15 min)

**You will:** read the 4-route helpdesk agent line-by-line so you can recite which keyword goes to which team — and why **order matters**.

### Step 1.1 — Move to the folder

```powershell
cd Phase2_Activities_and_Handlers\code\helpdesk_router
Get-ChildItem
code app.py
```

You should see at least:

```text
app.py
start_server.py
```

### Step 1.2 — Decode the 4 routes

Look at `app.py`. There are **4 handlers** in this order:

| # | Decorator | Matches |
|---|---|---|
| 1 | `@AGENT_APP.conversation_update("membersAdded")` | Welcome on join |
| 2 | `@AGENT_APP.message(IT_REGEX)` | regex `\b(reset\s+password\|locked\s+out\|mfa)\b` |
| 3 | `@AGENT_APP.message(HR_TRIGGERS)` | list `["payslip", "leave balance", "vacation days"]` |
| 4 | `@AGENT_APP.message(["expense", "invoice", "reimbursement"])` | exact keywords |
| 5 | `@AGENT_APP.activity("message")` | catch-all (always last!) |

> 🧠 **The Routing Rule:** the SDK tries handlers in the order they were defined. **The first one to match wins.** If you put the catch-all first, nothing else ever runs.

### Step 1.3 — Decode the regex

The IT route uses:

```python
IT_REGEX = re.compile(r"\b(reset\s+password|locked\s+out|mfa)\b", re.IGNORECASE)
```

Read it piece by piece:

| Piece | Means |
|---|---|
| `\b` | Word boundary — so "mfa" matches but not "comfartably". |
| `(a\|b\|c)` | Match a **or** b **or** c. |
| `\s+` | One or more whitespace characters. |
| `re.IGNORECASE` | "MFA", "Mfa", "mfa" all match. |

So this matches `reset password`, `Locked Out`, `MFA`, `reset    password` (with extra spaces) — but not `password reset` (different word order).

**What just happened?** You learned that an agent is just a **switchboard operator**. Every message comes in, and decorators tell the SDK "if it looks like this, ring *that* desk". The router itself is dumb — it just walks the handlers top-to-bottom and stops at the first match. Get the order wrong and the wrong desk picks up the phone.

### ✅ Checkpoint 1
You can point at each of the 5 handlers and say what triggers it. You understand that **order matters** — catch-all must be last.

---

## Lab 2 — Run it and test all routes (~10 min)

**You will:** start the router and prove all 4 desks (IT, HR, Finance, fallback) actually fire by sending one fake message per route.

### Step 2.1 — Start the agent

```powershell
python app.py
```

You should see `Running on http://localhost:3978`.

### Step 2.2 — Test each route from a 2nd terminal

Open a second terminal (`Ctrl+Shift+\``). We'll send 4 messages and watch the routing.

**Helper:** save a tiny PowerShell function so you don't have to retype the JSON every time:

```powershell
function Send-Msg {
    param([string]$Text)
    $body = @{
        type="message"; text=$Text
        from=@{id="user-1"; name="Alice"}; recipient=@{id="bot"}
        conversation=@{id="c-1"}; serviceUrl="http://localhost"
    } | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Uri http://localhost:3978/api/messages `
        -Method POST -ContentType "application/json" -Body $body
}
```

Now send 4 messages:

```powershell
Send-Msg "I forgot my password — locked out"   # → IT
Send-Msg "Send me my latest payslip"            # → HR
Send-Msg "Submit expense"                       # → Finance
Send-Msg "What's the weather?"                  # → Default menu
```

### Step 2.3 — Verify the routing in terminal 1

Switch back to terminal 1. You should see log lines like:

```text
INFO:helpdesk:Routing to IT
INFO:helpdesk:Routing to HR
INFO:helpdesk:Routing to Finance
```

The 4th message ("What's the weather?") hits the catch-all (no log line, but the user gets the menu back).

**What just happened?** You proved that the `Send-Msg` helper + log lines = a tiny **regression test suite**. Whenever you change the router, re-run these 4 messages and you instantly see if anything broke. This is the cheap-and-cheerful version of the unit tests you'll write in Phase 9.

### ✅ Checkpoint 2
Three INFO lines printed for the three matching messages. No INFO line for the fallback.

---

## Lab 3 — Break the routing order on purpose (~10 min)

**You will:** intentionally move the catch-all to the top, watch every route break, then put it back — so the routing rule is burned into your memory forever.

> 🎯 The goal of this lab is to feel — in your bones — why **order matters**.

### Step 3.1 — Stop the agent

In terminal 1, press `Ctrl+C`.

### Step 3.2 — Move the catch-all to the top

Open `app.py`. **Cut** (Ctrl+X) the entire catch-all block:

```python
@AGENT_APP.activity("message")
async def default(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity(
        f"I don't know how to help with: *{context.activity.text}*\n\n{MENU}"
    )
```

**Paste** it (Ctrl+V) **before** the IT regex handler. Save (`Ctrl+S`).

### Step 3.3 — Restart and re-test

```powershell
python app.py
```

In terminal 2:

```powershell
Send-Msg "reset password"
```

**What you'll see:** the agent replies with the *default menu* — the IT route never fires. Notice that terminal 1 shows **no** `Routing to IT` log line.

**Why?** The catch-all matches **every** message activity. Because we put it first, it wins for everything.

### Step 3.4 — Put it back

Move the catch-all block back to the **bottom** (after Finance). Save. Restart.

```powershell
Send-Msg "reset password"
```

Now `Routing to IT` prints again. ✅

**What just happened?** You broke the router on purpose, watched it fail in a predictable way, and fixed it — in less than 2 minutes. That's the **fastest debugging skill** in software: change one thing, see what breaks, change it back. Use this trick whenever you're not sure what a piece of code does.

### ✅ Checkpoint 3
You've personally experienced the routing-order rule and put the agent back to a working state.

---

## Lab 4 — Add a 4th team: Travel (~15 min)

**You will:** add a new route for travel-related messages.

### Step 4.1 — Define the route

In `app.py`, **before** the catch-all, add:

```python
# --- Travel: regex with optional "trip" word ---
TRAVEL_REGEX = re.compile(
    r"\b(book\s+(a\s+)?(flight|hotel|trip)|travel\s+request)\b",
    re.IGNORECASE,
)

@AGENT_APP.message(TRAVEL_REGEX)
async def route_travel(context: TurnContext, _state: TurnState) -> None:
    log.info("Routing to Travel")
    await context.send_activity(
        "✈️ Connecting you to **Travel**. Concur portal: https://aka.ms/concur"
    )
```

### Step 4.2 — Update the menu

Find `MENU = (...)` near the top. Add a line for Travel:

```python
MENU = (
    "👋 Hi! I'm the Contoso Help-Desk agent. Tell me what you need:\n"
    "- 🔐 *password*, *locked out* → IT\n"
    "- 💼 *payslip*, *leave balance* → HR\n"
    "- 💰 *expense*, *invoice* → Finance\n"
    "- ✈️ *book flight*, *book hotel*, *travel request* → Travel"
)
```

Save (`Ctrl+S`).

### Step 4.3 — Restart and test

```powershell
python app.py
```

In terminal 2:

```powershell
Send-Msg "I need to book a flight to Berlin"   # → Travel
Send-Msg "book hotel for next week"            # → Travel
Send-Msg "Submit travel request"               # → Travel
Send-Msg "trip to Spain please"                # → Default menu (no "book" keyword)
```

Verify the three matching ones print `Routing to Travel`.

**What just happened?** You added a brand-new desk to the switchboard without touching any existing code — because the SDK pattern is **add a decorator, you're done**. This is how real agents grow: keep stacking specific routes above the catch-all menu.

### ✅ Checkpoint 4
Travel works for the 3 expected phrases, and "trip to Spain please" falls through to the menu (as expected — the regex requires the word `book` or `travel request`).

> 💪 **Try this:** can you change the regex so "trip to Spain please" *also* routes to Travel? Hint: add another alternative inside the parentheses, like `|trip\s+to`.

---

## Lab 5 — Lifecycle handlers (~10 min)

**You will:** add handlers for two events you didn't see in Phase 1: someone *leaving* the chat, and the user *typing*.

### Step 5.1 — `membersRemoved`

Below the `welcome` handler in `app.py`, add:

```python
@AGENT_APP.conversation_update("membersRemoved")
async def on_leave(context: TurnContext, _state: TurnState) -> None:
    for m in context.activity.members_removed or []:
        log.info(f"👋 {m.name or m.id} left the conversation.")
```

### Step 5.2 — `typing`

Add this anywhere **before** the catch-all:

```python
@AGENT_APP.activity("typing")
async def on_typing(context: TurnContext, _state: TurnState) -> None:
    log.info(f"… {context.activity.from_property.name or 'someone'} is typing")
```

Save & restart.

### Step 5.3 — Fire the events from PowerShell

We can fake a "typing" activity:

```powershell
$body = @{
    type="typing"
    from=@{id="user-1"; name="Alice"}; recipient=@{id="bot"}
    conversation=@{id="c-1"}; serviceUrl="http://localhost"
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages `
    -Method POST -ContentType "application/json" -Body $body
```

Watch terminal 1 — you should see:

```text
INFO:helpdesk:… Alice is typing
```

And a "members removed":

```powershell
$body = @{
    type="conversationUpdate"
    membersRemoved=@(@{id="user-1"; name="Alice"})
    from=@{id="user-1"; name="Alice"}; recipient=@{id="bot"}
    conversation=@{id="c-1"}; serviceUrl="http://localhost"
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:3978/api/messages `
    -Method POST -ContentType "application/json" -Body $body
```

Terminal 1 should show:

```text
INFO:helpdesk:👋 Alice left the conversation.
```

**What just happened?** You learned that **not every activity is a message**. Teams sends `typing` while someone is mid-sentence and `membersRemoved` when someone leaves a meeting. The same decorator pattern handles them — just point at the activity type or sub-event you care about.

### ✅ Checkpoint 5
Both the `typing` and `membersRemoved` events show up in the logs.

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| Catch-all answers every message | You put `@AGENT_APP.activity("message")` *before* a specific `.message(...)`. | Move the catch-all to the bottom of the file. |
| The IT route doesn't fire for "Reset Password" | You forgot `re.IGNORECASE`. | Add the flag to the `re.compile(...)` call. |
| `re is not defined` | You removed the `import re` at the top. | Add `import re` to the imports. |
| Travel route fires for "I'm reading a book about flight school" | Your regex is too greedy. | Tighten with `\b` word boundaries (already in the example). |
| `Send-Msg : The term 'Send-Msg' is not recognized` | You defined the function in the *other* terminal. | Re-paste the `function Send-Msg { … }` block in your current terminal. |

---

## 🎓 Self-check

1. **In what order does the SDK try handlers?**

   <details><summary>Show answer</summary>
   The order they were registered (top-to-bottom in your file). First match wins.
   </details>

2. **Why does `@AGENT_APP.message(["hi", "hello"])` accept either word but `@AGENT_APP.message("hi hello")` does not?**

   <details><summary>Show answer</summary>
   The list form means "match any one of these". The string form is one exact string — `"hi hello"` would only match if the user typed exactly `hi hello`.
   </details>

3. **What's the difference between `members_added` and `members_removed`?**

   <details><summary>Show answer</summary>
   `members_added` fires when somebody joins the conversation; `members_removed` fires when somebody leaves. Both are sub-events of `conversation_update`.
   </details>

4. **Why do we always skip the bot's own ID when greeting?**

   <details><summary>Show answer</summary>
   The bot itself counts as a "member added" event. Without skipping `context.activity.recipient.id`, the bot would greet itself the moment it joins.
   </details>

5. **What does `re.IGNORECASE` do?**

   <details><summary>Show answer</summary>
   Makes the regex case-insensitive. `MFA`, `Mfa`, `mfa` all match.
   </details>

---

## 🚀 Bonus tasks

1. **Add a Legal route** — `re.compile(r"\b(contract|NDA|legal)\b", re.IGNORECASE)`. Don't forget to update the menu.
2. **Personal greeting** — change `welcome` to greet the user by name: `f"Hi {m.name}! ..."`.
3. **Suggested replies** — instead of just `MENU` text, return a list of buttons as a basic Adaptive Card. (Spoiler: that's Phase 4 — try if you're keen.)
4. **Log to a file** — replace the `logging.basicConfig(...)` line with one that writes to `helpdesk.log`. After 10 messages, open the file and see your routing history.

---

## 🏁 You're done!

You can now:

- Use all 4 handler decorators.
- Match with strings, lists, and regexes.
- Order routes correctly (specific → general).
- Handle lifecycle events like `membersAdded`, `membersRemoved`, `typing`.

Next → [Phase 3 — State & Storage (build a Shopping-Cart Agent)](../Phase3_State_and_Storage/README.md)
