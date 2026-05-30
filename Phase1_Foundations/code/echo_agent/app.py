# app.py
"""Echo Agent — Phase 1 sample.

What it does:
- Says "Welcome!" when a user joins.
- Replies with the help text if the user types "/help".
- Echoes anything else.

Run:
    python app.py

Then POST to http://localhost:3978/api/messages (see Phase1 README).

KID-FRIENDLY VERSION:
    Imagine a parrot in a cage. When you walk up, it says "Hi!".
    If you say "help", it tells you what it knows. If you say anything
    else, it copies you. That parrot is this file.
"""
# `from __future__ import annotations` = "I'm allowed to use the NEW way of
# writing types (like `list[int]` or `CloudAdapter | None`) even if Python
# is a little old." It's like telling the teacher "I'll use cursive even
# though we just learned print."
from __future__ import annotations

# `logging` = our diary. Instead of using `print()`, we write to a diary
# so we can choose later: show me everything, or only the bad stuff.
import logging

# Grab the Lego pieces we need from the SDK toy box:
from microsoft_agents.hosting.core import (
    AgentApplication,   # the agent BRAIN (where we hang handlers)
    MemoryStorage,      # a SHOEBOX to keep notes (forgets on restart)
    TurnContext,        # "this chat moment" (who said what, right now)
    TurnState,          # the sticky NOTE for this chat (the agent's memory)
)
# This file lives next to app.py. We borrow its `start_server` helper
# so we don't have to re-write the "phone line" plumbing every time.
from start_server import start_server

# 1. Configure logging so you can see what's happening.
#    Like setting the diary's font size + date stamp.
logging.basicConfig(
    level=logging.INFO,                                                # "show me INFO and louder"
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",          # diary line format
)
logger = logging.getLogger("echo_agent")  # our own pen, labelled "echo_agent"

# 2. Create the agent. MemoryStorage = forget everything on restart (OK for dev).
#    Think of MemoryStorage as a whiteboard that gets erased every morning.
AGENT_APP = AgentApplication(storage=MemoryStorage())


# 3. Greet new members.
#    `@AGENT_APP.conversation_update("membersAdded")` is a STICKER
#    that says: "Hey brain, run this function whenever a new person
#    joins the chat."
@AGENT_APP.conversation_update("membersAdded")
async def on_member_joined(context: TurnContext, state: TurnState) -> None:
    # `members_added` is a LIST of people who just joined. Could be empty.
    for member in context.activity.members_added or []:
        # Don't greet the bot itself (the bot is also a "member" of the chat).
        # That's why we skip the one whose id == the bot's own id.
        if member.id != context.activity.recipient.id:
            # `send_activity` = "please send this message back into the chat".
            await context.send_activity(
                f"👋 Welcome, {member.name or 'friend'}! "
                "Type anything and I'll echo it. Type /help for help."
            )


# 4. Respond to the literal text "/help".
#    `@AGENT_APP.message("/help")` is a sticker that says:
#    "Run this ONLY when the user types exactly /help."
@AGENT_APP.message("/help")
async def on_help(context: TurnContext, state: TurnState) -> None:
    await context.send_activity(
        "I'm a simple echo agent.\n"
        "- Type anything → I'll repeat it.\n"
        "- Type /help → you'll see this message."
    )


# 5. Catch-all: any message activity that didn't match anything above.
#    `@AGENT_APP.activity("message")` = "any chat message that wasn't
#    grabbed by a more specific handler above me".
@AGENT_APP.activity("message")
async def on_any_message(context: TurnContext, state: TurnState) -> None:
    # `context.activity.text` is what the user typed. Could be None if it
    # was a sticker or a card click — so we fall back to a friendly string.
    text = context.activity.text or "(empty message)"
    logger.info(f"Echoing back: {text!r}")                     # write to diary
    await context.send_activity(f"You said: {text}")           # parrot reply


# 6. Start the server (blocks forever).
#    `if __name__ == "__main__"` = "only run this if YOU started me directly".
if __name__ == "__main__":
    try:
        # Hand the brain to the phone line and start listening on port 3978.
        start_server(AGENT_APP, None)
    except Exception as error:
        # If anything explodes, write a full diary entry with the stack trace
        # before crashing — makes debugging much easier.
        logger.exception("Server crashed")
        raise
