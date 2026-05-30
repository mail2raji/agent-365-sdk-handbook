"""Confirmation card returned after a successful ticket submit.

KID-FRIENDLY VERSION:
    The receipt card. Title says "✅ Ticket TKT-XXXXXX created"; then a
    3-row FactSet (Title / Severity / Description-truncated). We trim the
    description to 140 chars so the card stays small in the chat.
"""
from __future__ import annotations


def build_ticket_confirmation(ticket_id: str, data: dict) -> dict:
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            # Big header with the new ticket id.
            {
                "type": "TextBlock",
                "text": f"✅ Ticket {ticket_id} created",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                # `FactSet` = tidy two-column "key: value" rows.
                "type": "FactSet",
                "facts": [
                    {"title": "Title",       "value": data.get("title", "")},
                    {"title": "Severity",    "value": data.get("severity", "")},
                    # `[:140]` slices to the first 140 chars (avoids huge cards).
                    {"title": "Description", "value": (data.get("body", "") or "")[:140]},
                ],
            },
        ],
    }
