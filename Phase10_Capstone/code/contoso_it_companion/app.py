"""Contoso IT Companion — Capstone scaffold.

Implement the TODOs to graduate. Refer to:
- Phase 4 (Adaptive Cards) for ticket form/confirmation.
- Phase 5 (LLM) for the chat loop.
- Phase 6 (Tools + RAG) for tool wiring.
- Phase 7 (Auth) for sign-in & Graph.
- Phase 8 (Agent 365) for OTel + identity.
"""
from __future__ import annotations

import logging
import os

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
log = logging.getLogger("contoso-it-companion")

# TODO Phase 8: configure OTel here (configure_otel(...))
# TODO Phase 3: swap MemoryStorage for BlobStorage in production.
# TODO Phase 7: pass `auth=MsalAuth(connection_name=...)` to AgentApplication.

AGENT_APP = AgentApplication(storage=MemoryStorage())


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "🛟 Hi! I'm the Contoso IT Companion. Try:\n"
                "• `help`\n"
                "• `login`\n"
                "• `who am i`\n"
                "• `policy <topic>`\n"
                "• `request ticket`"
            )


@AGENT_APP.message("help")
async def help_(context: TurnContext, state: TurnState):
    await context.send_activity(
        "Commands: `login`, `logout`, `who am i`, `policy <topic>`, `request ticket`, `my tickets`."
    )


# --- TODO Phase 7: implement login/logout/who-am-i with MSAL + Graph ---

# --- TODO Phase 6: implement RAG-backed policy lookup ---
# @AGENT_APP.message(re.compile(r"^policy\s+(.+)$", re.IGNORECASE))
# async def policy(context, state): ...

# --- TODO Phase 4: implement ticket form + submit handler ---
# @AGENT_APP.message("request ticket")
# async def show_form(context, state): ...
# @AGENT_APP.activity("message")
# async def maybe_submission(context, state):
#     if context.activity.value:
#         ...

# --- TODO Phase 5: implement fallback LLM chat ---
@AGENT_APP.activity("message")
async def fallback(context: TurnContext, state: TurnState):
    text = context.activity.text or ""
    await context.send_activity(
        f"(scaffold) I heard '{text}'. Implement the LLM and tool loop to answer properly."
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
