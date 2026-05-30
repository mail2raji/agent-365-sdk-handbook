"""AI Study Buddy — Phase 5 example.

KID-FRIENDLY VERSION:
    The agent is like a tutor who remembers what you've been asking.
    Each chat keeps a sticky note called `history` (the back-and-forth
    so far). When you ask a new question, the agent shows the WHOLE
    history to the LLM, gets a reply, and saves the new round.
    "reset" wipes the sticky note clean.
"""
from __future__ import annotations

import logging

# `dotenv` loads variables from a `.env` file into `os.environ`.
# So we can keep API keys OUT of the code and IN a private text file.
from dotenv import load_dotenv

from microsoft_agents.hosting.core import (
    AgentApplication,   # the BRAIN
    MemoryStorage,      # SHOEBOX of notes (forgets on restart)
    TurnContext,        # "this chat moment"
    TurnState,          # the sticky NOTE for this chat
)

from start_server import start_server
# `llm.py` lives next to this file. It wraps the OpenAI client.
from llm import ask

load_dotenv()                                       # read .env → env vars
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("buddy")

AGENT_APP = AgentApplication(storage=MemoryStorage())


def get_history(state: TurnState) -> list[dict]:
    # Helper: read the chat history list from the sticky note. Empty if missing.
    return state.conversation.get("history", [])


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "👋 Hi! I'm Buddy. Ask me a homework question. Type `reset` to forget our chat."
            )


@AGENT_APP.message("reset")
async def reset(context: TurnContext, state: TurnState):
    # Wipe the history sticky note clean.
    state.conversation["history"] = []
    await context.send_activity("🧹 Memory cleared. Ask me something new.")


@AGENT_APP.activity("message")
async def chat(context: TurnContext, state: TurnState):
    user_msg = context.activity.text or ""
    history = get_history(state)
    try:
        # `ask` adds both the user message AND the assistant reply to `history`
        # IN PLACE (mutates the list). We then save it back to state below.
        reply = await ask(history, user_msg)
    except Exception as e:
        # LLM call failed (network, quota, etc.) — tell the user instead of crashing.
        log.exception("LLM call failed")
        await context.send_activity(f"⚠️ Something went wrong: {e}")
        return
    # Re-save the (now-updated) history list to the sticky note.
    state.conversation["history"] = history
    await context.send_activity(reply)


if __name__ == "__main__":
    start_server(AGENT_APP, None)
