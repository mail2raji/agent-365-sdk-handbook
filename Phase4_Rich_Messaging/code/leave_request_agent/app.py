"""Leave-Request Approval Agent — Phase 4 example.

KID-FRIENDLY VERSION:
    Pretend the agent is the school office. A kid types "request leave".
    The agent slides a FORM (an Adaptive Card) across the desk: "why?,
    start date, end date, type". The kid fills it in and hits Submit.
    The agent gives back a CONFIRMATION card and writes the request in
    a notebook (`state.conversation['requests']`). Later, "list" prints
    everything from the notebook.
"""
from __future__ import annotations

# `uuid` = generates unique IDs (like a brand-new sticker every time).
# We use it to make request IDs like "LR-A1B2C3".
import uuid
import logging

from microsoft_agents.hosting.core import (
    AgentApplication,   # the BRAIN
    MemoryStorage,      # SHOEBOX of notes (forgets on restart)
    TurnContext,        # "this chat moment"
    TurnState,          # the sticky NOTE for this chat
)
# `Activity` = one envelope going in/out. `Attachment` = a card stapled to it.
from microsoft_agents.activity import Activity, ActivityTypes, Attachment

from start_server import start_server
# The two card builders live in their own file so this one stays short.
from cards.leave_request import build_leave_request_card, build_confirmation_card

# This MIME type tells Teams/Emulator: "the attachment is an Adaptive Card,
# please render it as a UI form (not as plain JSON)".
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
    # Build the card (just a Python dict) and staple it to a MESSAGE envelope.
    card = build_leave_request_card()
    await context.send_activity(
        Activity(
            type=ActivityTypes.MESSAGE,
            attachments=[Attachment(content_type=ADAPTIVE_CARD, content=card)],
        )
    )


@AGENT_APP.message("list")
async def list_requests(context: TurnContext, state: TurnState):
    # Read the notebook. If it's missing or empty, say so.
    requests = state.conversation.get("requests", [])
    if not requests:
        await context.send_activity("No requests yet.")
        return
    # Format each saved request as a bullet line.
    bullets = "\n".join(
        f"- **{r['id']}** {r['leave_type']} {r['start']} → {r['end']}" for r in requests
    )
    await context.send_activity(f"Your requests:\n{bullets}")


@AGENT_APP.activity("message")
async def on_any(context: TurnContext, state: TurnState):
    # 1. Card submission?
    #    When the user clicks Submit on the card, the SDK delivers a message
    #    activity with a `value` dict (the form fields) instead of text.
    if context.activity.value:
        data = dict(context.activity.value)
        # `action` is what we baked into Action.Submit.data on the card.
        if data.get("action") == "submit_leave":
            # Make a fresh ID like "LR-A1B2C3" (random hex chunk, uppercased).
            req_id = f"LR-{uuid.uuid4().hex[:6].upper()}"
            requests = state.conversation.get("requests", [])
            # `{**data, "id": req_id}` = copy all form fields + add an id.
            requests.append({"id": req_id, **data})
            state.conversation["requests"] = requests   # save to notebook
            log.info(f"Saved leave request {req_id}: {data}")

            # Build & send the confirmation card.
            confirm = build_confirmation_card(req_id, data)
            await context.send_activity(
                Activity(
                    type=ActivityTypes.MESSAGE,
                    attachments=[Attachment(content_type=ADAPTIVE_CARD, content=confirm)],
                )
            )
            return

    # 2. Plain text fallback — user typed something we don't recognise.
    await context.send_activity(
        "Type `request leave` to start, or `list` to see your requests."
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
