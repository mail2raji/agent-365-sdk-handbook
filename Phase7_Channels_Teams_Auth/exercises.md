# 🧩 Phase 7 — Exercises

## Exercise 1 — Two identities

Name the two identities involved in an agent and what each proves.

<details><summary>Answer</summary>

- **Agent identity** (Bot App Registration) proves the agent is allowed to talk to the Bot Service.
- **User identity** (OAuth/MSAL) proves *who* the user is, so the agent can act on their behalf (e.g. read their mail).

</details>

---

## Exercise 2 — Same code, many channels

Why can the same `AgentApplication` serve Teams, Web Chat, and email without per-channel forks?

<details><summary>Answer</summary>

The Bot Service normalizes all inbound traffic into the unified `Activity` model. Your handlers see the same shape regardless of channel; the SDK and Bot Service translate to/from each channel's native format.

</details>

---

## Exercise 3 — Branch on channel

Add a handler that says "Welcome to Teams 🤝" only when the channel is Teams.

<details><summary>Answer</summary>

```python
@AGENT_APP.conversation_update("membersAdded")
async def teams_welcome(context, state):
    if context.activity.channel_id == "msteams":
        await context.send_activity("Welcome to Teams 🤝")
```

</details>

---

## Exercise 4 — Manifest scopes

What do `personal`, `team`, and `groupchat` scopes in `manifest.json` enable?

<details><summary>Answer</summary>

- `personal` — 1:1 chat with the bot.
- `team` — install in a team / channel.
- `groupchat` — install in a multi-person group chat.

</details>

---

## Exercise 5 — Redirect URI

Why must the Entra app redirect URI be `https://token.botframework.com/.auth/web/redirect`?

<details><summary>Answer</summary>

The Azure Bot Service handles the OAuth dance for you and exchanges the code at *that* URL. Your bot never sees the auth code — only the resulting token.

</details>

---

## Exercise 6 — Get token

In any handler, how do you get the signed-in user's access token?

<details><summary>Answer</summary>

```python
token = await AUTH.get_token(context)
```

Returns `None` if not signed in. Trigger sign-in with `await AUTH.sign_in(context, state)`.

</details>

---

## Exercise 7 — Add a Graph call

Add a `messages` command that lists the subjects of the user's 5 most recent emails.

<details><summary>Answer</summary>

```python
@AGENT_APP.message("messages")
async def messages(context, state):
    token = await _get_token(context)
    if not token:
        await context.send_activity("Please `login` first.")
        return
    async with httpx.AsyncClient(timeout=20) as http:
        r = await http.get(
            "https://graph.microsoft.com/v1.0/me/messages?$top=5&$select=subject",
            headers={"Authorization": f"Bearer {token}"},
        )
    subs = [m["subject"] for m in r.json().get("value", [])]
    await context.send_activity("📬 Latest:\n• " + "\n• ".join(subs))
```

</details>

---

## Exercise 8 — Scope required

You want to read a user's calendar. Which delegated scope do you add?

<details><summary>Answer</summary>

`Calendars.Read`. Add it in Entra → API permissions, and to the scopes string in the OAuth connection settings.

</details>

---

## Exercise 9 — Why MSAL?

Why use MSAL instead of writing raw OAuth flows?

<details><summary>Answer</summary>

MSAL handles token acquisition, caching, refresh, account selection, and PKCE. Rolling your own is error-prone and a security risk.

</details>

---

## Exercise 10 — Localhost limitation

Why can't you test full SSO purely on `http://localhost:3978`?

<details><summary>Answer</summary>

The Bot Service must reach your bot over **HTTPS** and your bot's messaging endpoint must be publicly reachable so it can receive activities including the post-OAuth `tokens/response` activity. Use dev tunnels or ngrok.

</details>

---

## Exercise 11 — Tunnels

What's a quick way to expose your local agent publicly during development?

<details><summary>Answer</summary>

VS Code: `code tunnel` or the **Ports** panel → forward port 3978 → make Public. Alternatively `ngrok http 3978`. Update the Bot Messaging endpoint to `https://<host>/api/messages`.

</details>

---

## Exercise 12 — Manifest id

Where does the `botId` in `manifest.json` come from?

<details><summary>Answer</summary>

It's the **Microsoft App ID** of the Azure Bot resource (a GUID). Without matching ids the Teams client cannot route messages to your bot.

</details>

---

## Exercise 13 — Sign out

What does `auth.sign_out(context, state)` do?

<details><summary>Answer</summary>

It clears the SDK's cached token store entry for the current user/connection. Next time they ask for a token, they have to sign in again.

</details>

---

## Exercise 14 — Bonus: Teams mention

Send a message that explicitly mentions the current user (only on Teams).

<details><summary>Answer</summary>

```python
from microsoft_agents.hosting.teams import TeamsActivityHelpers

if context.activity.channel_id == "msteams":
    await context.send_activity(TeamsActivityHelpers.mention(context, "Hi!"))
else:
    await context.send_activity("Hi!")
```

</details>

---

## Exercise 15 — Bonus: proactive ping

Sketch how the agent could send a Teams DM to a user *without* them messaging first (proactive notification).

<details><summary>Answer</summary>

1. When the user first interacts, store `context.activity.conversation.reference` (call `TurnContext.get_conversation_reference`).
2. Later (e.g. from a background job) call `adapter.continue_conversation(ref, callback)` where `callback(turn_context)` sends the message.
3. The Azure Bot resource delivers the message to Teams.

</details>

---

✅ Next → **[Phase 8 — Agent 365 enterprise layer](../Phase8_Agent365_Enterprise/README.md)** — the *other* SDK and what it adds.
