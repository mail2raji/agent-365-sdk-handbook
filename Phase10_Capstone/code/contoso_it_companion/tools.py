"""Tool implementations for the capstone.

TODO: replace mocks with real integrations.
"""
from __future__ import annotations

import uuid
from typing import Any

# In-memory ticket store for the demo; in production POST to ServiceNow / Jira.
TICKETS: list[dict[str, Any]] = []


def create_ticket(title: str, severity: str, body: str) -> str:
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    TICKETS.append({"id": ticket_id, "title": title, "severity": severity, "body": body})
    return f"Created ticket {ticket_id} ({severity}): {title}"


def list_tickets() -> str:
    if not TICKETS:
        return "No tickets yet."
    return "\n".join(f"- {t['id']} [{t['severity']}] {t['title']}" for t in TICKETS)


async def get_my_profile(token: str) -> str:
    """TODO Phase 7: call Microsoft Graph /me using `token`."""
    return "TODO: call Graph /me here"


async def lookup_policy(question: str) -> str:
    """TODO Phase 6: call rag.search(question)."""
    return f"TODO: look up '{question}' in the policy docs."


# Schemas (Phase 6 style)
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
