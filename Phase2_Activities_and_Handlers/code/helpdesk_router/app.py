"""Help-Desk Router — Phase 2 example.

Routes employee messages to the right department based on keywords.

Run:
    python app.py

KID-FRIENDLY VERSION:
    Pretend the agent is the front-desk teacher at school. A kid walks up
    and says "I lost my password" → teacher points to the IT room.
    A kid says "I want my payslip" → teacher points to HR. If the teacher
    doesn't understand, she shows the kid the big sign on the wall (MENU).
"""
# `from __future__ import annotations` = let me use new-style type hints.
from __future__ import annotations

# `re` = the REGULAR-EXPRESSION toy. It's like a magnifying glass that
# searches text for patterns (e.g. "the word reset followed by password").
import re
# `logging` = our diary.
import logging

from microsoft_agents.hosting.core import (
    AgentApplication,   # the BRAIN
    MemoryStorage,      # SHOEBOX of sticky notes (lost on restart)
    TurnContext,        # "this chat moment"
    TurnState,          # the sticky NOTE for this chat
)
from start_server import start_server   # "phone line + lemonade stand" helper

# Set up the diary: show INFO and louder, with timestamps.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("helpdesk")  # diary pen labelled "helpdesk"

# Build the agent brain with a forget-on-restart shoebox.
AGENT_APP = AgentApplication(storage=MemoryStorage())


# The big sign on the wall — reused in two places below.
MENU = (
    "👋 Hi! I'm the Contoso Help-Desk agent. Tell me what you need:\n"
    "- 🔐 *password*, *locked out* → IT\n"
    "- 💼 *payslip*, *leave balance* → HR\n"
    "- 💰 *expense*, *invoice* → Finance"
)


# --- Welcome ---
# Run this whenever someone NEW joins the chat.
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, _state: TurnState) -> None:
    # `members_added` could include the bot itself — skip it.
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(MENU)


# --- IT: regex with case-insensitive flag ---
# `re.compile(...)` = build the magnifying glass ONCE so it's fast every time.
# `\b` means "word boundary" (so it doesn't match "resetpassword" smashed together).
# `re.IGNORECASE` = it matches "Reset", "RESET", "reset" — all the same.
IT_REGEX = re.compile(r"\b(reset\s+password|locked\s+out|mfa)\b", re.IGNORECASE)


# Sticker: "run me if the user's message MATCHES this magnifying glass".
@AGENT_APP.message(IT_REGEX)
async def route_it(context: TurnContext, _state: TurnState) -> None:
    log.info("Routing to IT")    # write to diary so we can debug later
    await context.send_activity(
        "🔐 Connecting you to **IT**. Reset link: https://aka.ms/reset"
    )


# --- HR: list of keywords ---
# A LIST of plain strings — the SDK checks "does the message contain ANY of these?"
HR_TRIGGERS = ["payslip", "leave balance", "vacation days"]


@AGENT_APP.message(HR_TRIGGERS)
async def route_hr(context: TurnContext, _state: TurnState) -> None:
    log.info("Routing to HR")
    await context.send_activity("💼 Connecting you to **HR**. Check the HR portal.")


# --- Finance: exact words ---
# You can pass the list INLINE instead of saving it to a variable first.
@AGENT_APP.message(["expense", "invoice", "reimbursement"])
async def route_finance(context: TurnContext, _state: TurnState) -> None:
    log.info("Routing to Finance")
    await context.send_activity("💰 Connecting you to **Finance**.")


# --- Default: show menu (catch-all, registered LAST) ---
# `@AGENT_APP.activity("message")` = catch ANY message that no handler above grabbed.
# Order matters: this MUST be the last `.message`/`.activity("message")` we register.
@AGENT_APP.activity("message")
async def default(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity(
        f"I don't know how to help with: *{context.activity.text}*\n\n{MENU}"
    )


# Only run the server if YOU started this file directly.
if __name__ == "__main__":
    start_server(AGENT_APP, None)
