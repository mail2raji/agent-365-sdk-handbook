"""Confirmation card returned after a successful ticket submit."""
from __future__ import annotations


def build_ticket_confirmation(ticket_id: str, data: dict) -> dict:
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": f"✅ Ticket {ticket_id} created",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Title", "value": data.get("title", "")},
                    {"title": "Severity", "value": data.get("severity", "")},
                    {"title": "Description", "value": (data.get("body", "") or "")[:140]},
                ],
            },
        ],
    }
