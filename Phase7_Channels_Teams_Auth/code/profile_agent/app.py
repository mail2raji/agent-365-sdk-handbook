"""Profile Agent — Phase 7.

Demonstrates channel awareness + OAuth SSO + Microsoft Graph.

NOTE: full SSO needs a public HTTPS endpoint and an Azure Bot OAuth Connection.
Locally this still loads and replies; sign-in just fails gracefully.

KID-FRIENDLY VERSION:
    This agent learns who YOU are. The user types `login`, the agent
    pops up a Microsoft sign-in card, the user signs in, and we get a
    "badge" (an access token) we can show to Microsoft Graph to ask:
    "who is this person?" or "what mail folders do they have?".
    `logout` rips the badge up.
"""
from __future__ import annotations

import logging
import os

# `httpx` = a modern HTTP client (like `requests`, but async-friendly).
# We use it to call Microsoft Graph.
import httpx
from dotenv import load_dotenv

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)

from start_server import start_server

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("profile-agent")

# MSAL auth is optional at import time so this file still runs locally without it.
# `try/except` = "try to plug in the auth piece; if it isn't installed,
# just log a warning and continue without it".
try:
    from microsoft_agents.authentication.msal import MsalAuth  # type: ignore
    # `connection_name` matches the OAuth Connection you created on your Bot.
    AUTH = MsalAuth(connection_name=os.environ.get("OAUTH_CONNECTION_NAME", "graph-sso"))
except Exception as e:  # noqa: BLE001
    log.warning("MSAL auth unavailable: %s", e)
    AUTH = None

# Notice we pass `auth=AUTH` to the brain. The SDK uses it for `sign_in`/`sign_out`.
AGENT_APP = AgentApplication(storage=MemoryStorage(), auth=AUTH)


async def _get_token(context: TurnContext) -> str | None:
    # Helper: return the user's access token, or None if not signed in / no auth.
    if AUTH is None:
        return None
    try:
        return await AUTH.get_token(context)
    except Exception:  # noqa: BLE001
        return None


# ---------- handlers ----------
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "👋 Hi! Commands:\n"
                "• `login` — sign in with your work account\n"
                "• `me` — show your profile\n"
                "• `folders` — list your mailbox folders\n"
                "• `logout` — sign out"
            )


@AGENT_APP.message("login")
async def login(context: TurnContext, state: TurnState):
    if AUTH is None:
        await context.send_activity("Auth not configured. Set OAUTH_CONNECTION_NAME and configure the Azure Bot OAuth connection.")
        return
    token = await _get_token(context)
    if token:
        # Already signed in — no need to bother the user again.
        await context.send_activity("✅ You're already signed in.")
        return
    # `sign_in` makes the SDK send the special OAuth card so the user can sign in.
    await AUTH.sign_in(context, state)  # SDK sends the OAuth card


@AGENT_APP.message("logout")
async def logout(context: TurnContext, state: TurnState):
    if AUTH is None:
        await context.send_activity("Auth not configured.")
        return
    await AUTH.sign_out(context, state)
    await context.send_activity("👋 Signed out.")


@AGENT_APP.message("me")
async def me(context: TurnContext, state: TurnState):
    token = await _get_token(context)
    if not token:
        await context.send_activity("Please `login` first.")
        return
    # `async with httpx.AsyncClient(...)` = make a connection, do the call,
    # then automatically close it (like `with open(...)` for files).
    async with httpx.AsyncClient(timeout=20) as http:
        r = await http.get(
            "https://graph.microsoft.com/v1.0/me",
            # The token is the BADGE we got from sign-in. Bearer = "I'm allowed".
            headers={"Authorization": f"Bearer {token}"},
        )
    if r.status_code != 200:
        await context.send_activity(f"Graph error {r.status_code}: {r.text}")
        return
    data = r.json()
    # `mail` may be missing for personal accounts — fall back to UPN.
    await context.send_activity(
        f"**{data.get('displayName')}** — {data.get('mail') or data.get('userPrincipalName')}"
    )


@AGENT_APP.message("folders")
async def folders(context: TurnContext, state: TurnState):
    token = await _get_token(context)
    if not token:
        await context.send_activity("Please `login` first.")
        return
    async with httpx.AsyncClient(timeout=20) as http:
        r = await http.get(
            "https://graph.microsoft.com/v1.0/me/mailFolders",
            headers={"Authorization": f"Bearer {token}"},
        )
    if r.status_code != 200:
        await context.send_activity(f"Graph error {r.status_code}: {r.text}")
        return
    # Graph wraps results in `{ "value": [...] }`. Extract folder names.
    names = [f["displayName"] for f in r.json().get("value", [])]
    if not names:
        await context.send_activity("No folders found.")
        return
    await context.send_activity("📂 Folders:\n• " + "\n• ".join(names))


@AGENT_APP.activity("message")
async def fallback(context: TurnContext, state: TurnState):
    # `channel_id` tells you WHERE the chat is coming from: "emulator", "msteams",
    # "webchat", etc. Great for tailoring the experience.
    channel = context.activity.channel_id
    await context.send_activity(
        f"You're chatting via **{channel}**. Try `login`, `me`, or `folders`."
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
