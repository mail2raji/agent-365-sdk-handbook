"""AI Study Buddy — Phase 5 example."""
from __future__ import annotations

import logging

from dotenv import load_dotenv

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)

from start_server import start_server
from llm import ask

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("buddy")

AGENT_APP = AgentApplication(storage=MemoryStorage())


def get_history(state: TurnState) -> list[dict]:
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
    state.conversation["history"] = []
    await context.send_activity("🧹 Memory cleared. Ask me something new.")


@AGENT_APP.activity("message")
async def chat(context: TurnContext, state: TurnState):
    user_msg = context.activity.text or ""
    history = get_history(state)
    try:
        reply = await ask(history, user_msg)
    except Exception as e:
        log.exception("LLM call failed")
        await context.send_activity(f"⚠️ Something went wrong: {e}")
        return
    state.conversation["history"] = history
    await context.send_activity(reply)


if __name__ == "__main__":
    start_server(AGENT_APP, None)
