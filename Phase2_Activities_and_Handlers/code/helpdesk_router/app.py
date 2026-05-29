"""Help-Desk Router — Phase 2 example.

Routes employee messages to the right department based on keywords.

Run:
    python app.py
"""
from __future__ import annotations

import re
import logging

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from start_server import start_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("helpdesk")

AGENT_APP = AgentApplication(storage=MemoryStorage())


MENU = (
    "👋 Hi! I'm the Contoso Help-Desk agent. Tell me what you need:\n"
    "- 🔐 *password*, *locked out* → IT\n"
    "- 💼 *payslip*, *leave balance* → HR\n"
    "- 💰 *expense*, *invoice* → Finance"
)


# --- Welcome ---
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, _state: TurnState) -> None:
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(MENU)


# --- IT: regex with case-insensitive flag ---
IT_REGEX = re.compile(r"\b(reset\s+password|locked\s+out|mfa)\b", re.IGNORECASE)


@AGENT_APP.message(IT_REGEX)
async def route_it(context: TurnContext, _state: TurnState) -> None:
    log.info("Routing to IT")
    await context.send_activity(
        "🔐 Connecting you to **IT**. Reset link: https://aka.ms/reset"
    )


# --- HR: list of keywords ---
HR_TRIGGERS = ["payslip", "leave balance", "vacation days"]


@AGENT_APP.message(HR_TRIGGERS)
async def route_hr(context: TurnContext, _state: TurnState) -> None:
    log.info("Routing to HR")
    await context.send_activity("💼 Connecting you to **HR**. Check the HR portal.")


# --- Finance: exact words ---
@AGENT_APP.message(["expense", "invoice", "reimbursement"])
async def route_finance(context: TurnContext, _state: TurnState) -> None:
    log.info("Routing to Finance")
    await context.send_activity("💰 Connecting you to **Finance**.")


# --- Default: show menu (catch-all, registered LAST) ---
@AGENT_APP.activity("message")
async def default(context: TurnContext, _state: TurnState) -> None:
    await context.send_activity(
        f"I don't know how to help with: *{context.activity.text}*\n\n{MENU}"
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
