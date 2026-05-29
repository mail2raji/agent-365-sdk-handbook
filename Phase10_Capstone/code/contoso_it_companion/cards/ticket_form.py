"""Adaptive Card for raising a ticket. TODO: extend the schema."""
from __future__ import annotations


def build_ticket_form() -> dict:
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": "Raise a ticket", "weight": "Bolder", "size": "Medium"},
            {"type": "Input.Text", "id": "title", "label": "Title", "isRequired": True, "errorMessage": "Title is required."},
            {
                "type": "Input.ChoiceSet",
                "id": "severity",
                "label": "Severity",
                "value": "P3",
                "choices": [
                    {"title": "P1 - critical", "value": "P1"},
                    {"title": "P2 - high", "value": "P2"},
                    {"title": "P3 - normal", "value": "P3"},
                    {"title": "P4 - low", "value": "P4"},
                ],
            },
            {"type": "Input.Text", "id": "body", "label": "Description", "isMultiline": True},
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Submit",
                "data": {"action": "submit_ticket"},
            }
        ],
    }
