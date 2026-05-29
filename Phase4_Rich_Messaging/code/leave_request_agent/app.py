"""Leave-Request Approval Agent — Phase 4 example."""
from __future__ import annotations

import uuid
import logging

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft_agents.activity import Activity, ActivityTypes, Attachment

from start_server import start_server
from cards.leave_request import build_leave_request_card, build_confirmation_card

ADAPTIVE_CARD = "application/vnd.microsoft.card.adaptive"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("leave")

AGENT_APP = AgentApplication(storage=MemoryStorage())


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "Type `request leave` to open the leave form, or `list` to see your requests."
            )


@AGENT_APP.message("request leave")
async def show_form(context: TurnContext, state: TurnState):
    card = build_leave_request_card()
    await context.send_activity(
        Activity(
            type=ActivityTypes.MESSAGE,
            attachments=[Attachment(content_type=ADAPTIVE_CARD, content=card)],
        )
    )


@AGENT_APP.message("list")
async def list_requests(context: TurnContext, state: TurnState):
    requests = state.conversation.get("requests", [])
    if not requests:
        await context.send_activity("No requests yet.")
        return
    bullets = "\n".join(
        f"- **{r['id']}** {r['leave_type']} {r['start']} → {r['end']}" for r in requests
    )
    await context.send_activity(f"Your requests:\n{bullets}")


@AGENT_APP.activity("message")
async def on_any(context: TurnContext, state: TurnState):
    # 1. Card submission?
    if context.activity.value:
        data = dict(context.activity.value)
        if data.get("action") == "submit_leave":
            req_id = f"LR-{uuid.uuid4().hex[:6].upper()}"
            requests = state.conversation.get("requests", [])
            requests.append({"id": req_id, **data})
            state.conversation["requests"] = requests
            log.info(f"Saved leave request {req_id}: {data}")

            confirm = build_confirmation_card(req_id, data)
            await context.send_activity(
                Activity(
                    type=ActivityTypes.MESSAGE,
                    attachments=[Attachment(content_type=ADAPTIVE_CARD, content=confirm)],
                )
            )
            return

    # 2. Plain text fallback
    await context.send_activity(
        "Type `request leave` to start, or `list` to see your requests."
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
