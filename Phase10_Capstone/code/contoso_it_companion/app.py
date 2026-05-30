"""Contoso IT Companion — Capstone scaffold.

Implement the TODOs to graduate. Refer to:
- Phase 4 (Adaptive Cards) for ticket form/confirmation.
- Phase 5 (LLM) for the chat loop.
- Phase 6 (Tools + RAG) for tool wiring.
- Phase 7 (Auth) for sign-in & Graph.
- Phase 8 (Agent 365) for OTel + identity.

KID-FRIENDLY VERSION:
    This is a HALF-BUILT Lego model. The frame is here; the colourful
    bricks are TODO comments. Your homework is to bring the pieces from
    earlier phases and snap them in: cards (Phase 4), LLM (Phase 5),
    tools+RAG (Phase 6), auth (Phase 7), enterprise wrap (Phase 8).
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv          # read .env → os.environ

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
#   → wire OpenTelemetry so every chat shows up as a trace in App Insights.
# TODO Phase 3: swap MemoryStorage for BlobStorage in production.
#   → today the agent forgets on restart. In production, save to Azure Blob.
# TODO Phase 7: pass `auth=MsalAuth(connection_name=...)` to AgentApplication.
#   → add real Microsoft sign-in so we can call Graph as the user.

AGENT_APP = AgentApplication(storage=MemoryStorage())


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    # Greet every new joiner with the command menu.
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
#   → Copy the `@AGENT_APP.message("login")` etc. handlers from
#     Phase7_Channels_Teams_Auth/code/profile_agent/app.py.

# --- TODO Phase 6: implement RAG-backed policy lookup ---
# @AGENT_APP.message(re.compile(r"^policy\s+(.+)$", re.IGNORECASE))
# async def policy(context, state): ...
#   → Match "policy <anything>", call rag.search(<anything>), reply with hits.

# --- TODO Phase 4: implement ticket form + submit handler ---
# @AGENT_APP.message("request ticket")
# async def show_form(context, state): ...
#   → Send `build_ticket_form()` as an Adaptive Card attachment.
# @AGENT_APP.activity("message")
# async def maybe_submission(context, state):
#     if context.activity.value:
#         ...
#   → When the user clicks Submit, `activity.value` is the form dict.
#     Call `tools.create_ticket(...)` and reply with `build_ticket_confirmation(...)`.

# --- TODO Phase 5: implement fallback LLM chat ---
@AGENT_APP.activity("message")
async def fallback(context: TurnContext, state: TurnState):
    # Today this just echoes a placeholder. Your job: replace with the
    # Phase 6 tool-loop so unrecognised messages go to the LLM with tools.
    text = context.activity.text or ""
    await context.send_activity(
        f"(scaffold) I heard '{text}'. Implement the LLM and tool loop to answer properly."
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
