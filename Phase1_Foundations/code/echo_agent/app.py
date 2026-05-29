# app.py
"""Echo Agent — Phase 1 sample.

What it does:
- Says "Welcome!" when a user joins.
- Replies with the help text if the user types "/help".
- Echoes anything else.

Run:
    python app.py

Then POST to http://localhost:3978/api/messages (see Phase1 README).
"""
from __future__ import annotations

import logging

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from start_server import start_server

# 1. Configure logging so you can see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("echo_agent")

# 2. Create the agent. MemoryStorage = forget everything on restart (OK for dev).
AGENT_APP = AgentApplication(storage=MemoryStorage())


# 3. Greet new members
@AGENT_APP.conversation_update("membersAdded")
async def on_member_joined(context: TurnContext, state: TurnState) -> None:
    for member in context.activity.members_added or []:
        # Don't greet the bot itself
        if member.id != context.activity.recipient.id:
            await context.send_activity(
                f"👋 Welcome, {member.name or 'friend'}! "
                "Type anything and I'll echo it. Type /help for help."
            )


# 4. Respond to the literal text "/help"
@AGENT_APP.message("/help")
async def on_help(context: TurnContext, state: TurnState) -> None:
    await context.send_activity(
        "I'm a simple echo agent.\n"
        "- Type anything → I'll repeat it.\n"
        "- Type /help → you'll see this message."
    )


# 5. Catch-all: any message activity that didn't match anything above
@AGENT_APP.activity("message")
async def on_any_message(context: TurnContext, state: TurnState) -> None:
    text = context.activity.text or "(empty message)"
    logger.info(f"Echoing back: {text!r}")
    await context.send_activity(f"You said: {text}")


# 6. Start the server (blocks forever)
if __name__ == "__main__":
    try:
        start_server(AGENT_APP, None)
    except Exception as error:
        logger.exception("Server crashed")
        raise
