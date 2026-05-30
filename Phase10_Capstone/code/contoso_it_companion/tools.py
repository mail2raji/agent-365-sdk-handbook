"""Tool implementations for the capstone.

TODO: replace mocks with real integrations.

KID-FRIENDLY VERSION:
    Two "tools" the LLM is allowed to call:
      1. create_ticket — makes a new fake ticket in `TICKETS`.
      2. lookup_policy — today returns a placeholder. Replace with a
         real RAG search from Phase 6.
    Each tool has a Python FUNCTION + a SCHEMA (the menu entry the LLM sees).
"""
from __future__ import annotations

import uuid                       # to mint unique ticket IDs
from typing import Any

# In-memory ticket store for the demo; in production POST to ServiceNow / Jira.
# This list lives ONLY in this process — if you restart, it forgets.
TICKETS: list[dict[str, Any]] = []


def create_ticket(title: str, severity: str, body: str) -> str:
    # Make a fresh ID like "TKT-A1B2C3" using a random hex chunk.
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    TICKETS.append({"id": ticket_id, "title": title, "severity": severity, "body": body})
    return f"Created ticket {ticket_id} ({severity}): {title}"


def list_tickets() -> str:
    if not TICKETS:
        return "No tickets yet."
    # Pretty bullet list, one line per ticket.
    return "\n".join(f"- {t['id']} [{t['severity']}] {t['title']}" for t in TICKETS)


async def get_my_profile(token: str) -> str:
    """TODO Phase 7: call Microsoft Graph /me using `token`.

    Replace this with the `httpx.AsyncClient(...).get("/me", headers=...)` from Phase 7.
    """
    return "TODO: call Graph /me here"


async def lookup_policy(question: str) -> str:
    """TODO Phase 6: call rag.search(question).

    Replace this with a real VectorStore.search() lookup from Phase 6.
    """
    return f"TODO: look up '{question}' in the policy docs."


# Schemas (Phase 6 style) — the MENU we hand the LLM. Each entry says:
# "here's a tool name, here's what it does, here are the arguments."
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create an IT support ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    # `enum` = restrict severity to these 4 strings only.
                    "severity": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
                    "body": {"type": "string"},
                },
                "required": ["title", "severity", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_policy",
            "description": "Search the company policy knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
]
