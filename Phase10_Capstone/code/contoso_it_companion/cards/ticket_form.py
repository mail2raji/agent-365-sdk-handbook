"""Adaptive Card for raising a ticket. TODO: extend the schema.

KID-FRIENDLY VERSION:
    The RECIPE for the "raise a ticket" form: title input, severity
    dropdown (P1–P4), big multi-line description, and a Submit button.
    Teams reads this dict and bakes a pretty form on screen.
"""
from __future__ import annotations


def build_ticket_form() -> dict:
    return {
        # Every Adaptive Card needs a $schema + a version.
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            # H2-ish header.
            {"type": "TextBlock", "text": "Raise a ticket", "weight": "Bolder", "size": "Medium"},
            # Single-line text input. `id` is the KEY we'll read on Submit.
            {"type": "Input.Text", "id": "title", "label": "Title", "isRequired": True, "errorMessage": "Title is required."},
            {
                # Compact dropdown. `value` = pre-selected option.
                "type": "Input.ChoiceSet",
                "id": "severity",
                "label": "Severity",
                "value": "P3",
                "choices": [
                    {"title": "P1 - critical", "value": "P1"},
                    {"title": "P2 - high",     "value": "P2"},
                    {"title": "P3 - normal",   "value": "P3"},
                    {"title": "P4 - low",      "value": "P4"},
                ],
            },
            # `isMultiline=True` = a tall text area (great for descriptions).
            {"type": "Input.Text", "id": "body", "label": "Description", "isMultiline": True},
        ],
        # The Submit button bundles all `id` values + `data` into
        # `activity.value` so the agent can read them.
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Submit",
                "data": {"action": "submit_ticket"},     # used to identify which form
            }
        ],
    }
