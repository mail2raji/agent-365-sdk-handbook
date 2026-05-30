"""Adaptive Card builders for the Leave-Request Agent.

KID-FRIENDLY VERSION:
    An Adaptive Card is just a Python DICT shaped like a recipe.
    Teams (or the Emulator) reads the recipe and bakes a pretty form
    on screen — text input, date picker, dropdown, Submit button.
    These two builder functions return the recipes. We keep them in
    their own file so app.py stays short and readable.
"""
from __future__ import annotations


def build_leave_request_card() -> dict:
    """Return the JSON dict for the leave-request input card.

    Returns the RECIPE for the form: title, 3 inputs, 1 dropdown, 1 Submit.
    """
    return {
        # Every Adaptive Card starts with `type=AdaptiveCard` + a `$schema`
        # pointing to the official spec + a `version` number.
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        # `body` = the ROWS the user sees (top → bottom).
        "body": [
            {
                # A big bold title — like the H1 on a webpage.
                "type": "TextBlock",
                "size": "Large",
                "weight": "Bolder",
                "text": "📝 Request Time Off",
            },
            {
                # A text box. `id` is the KEY we'll read on Submit.
                # `isRequired=True` blocks Submit until the user types something.
                "type": "Input.Text",
                "id": "reason",
                "label": "Reason",
                "placeholder": "Why are you taking leave?",
                "isRequired": True,
                "errorMessage": "Please provide a reason.",
            },
            {
                # A built-in date picker. No code, just a property.
                "type": "Input.Date",
                "id": "start",
                "label": "Start date",
                "isRequired": True,
                "errorMessage": "Start date is required.",
            },
            {
                "type": "Input.Date",
                "id": "end",
                "label": "End date",
                "isRequired": True,
                "errorMessage": "End date is required.",
            },
            {
                # A dropdown. `value` = the pre-selected option.
                # Each choice has a friendly `title` and a machine-readable `value`.
                "type": "Input.ChoiceSet",
                "id": "leave_type",
                "label": "Type",
                "style": "compact",
                "value": "vacation",
                "choices": [
                    {"title": "Vacation", "value": "vacation"},
                    {"title": "Sick",     "value": "sick"},
                    {"title": "Personal", "value": "personal"},
                ],
            },
        ],
        # `actions` = buttons at the bottom.
        # `Action.Submit` collects all `id` values + `data` into the message's
        # `activity.value` dict so our agent can read them.
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Submit",
                "data": {"action": "submit_leave"},   # used to identify which form
            }
        ],
    }


def build_confirmation_card(request_id: str, data: dict) -> dict:
    """Confirmation card shown after submission.

    Returns a RECEIPT-style card: title + 4-row fact table + small footnote.
    """
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "size": "Large",
                "weight": "Bolder",
                "text": f"✅ Request {request_id} submitted",
            },
            {
                # `FactSet` = a tidy two-column table of "title: value" rows.
                # Perfect for receipts and confirmations.
                "type": "FactSet",
                "facts": [
                    {"title": "Reason", "value": data.get("reason", "")},
                    {"title": "Start",  "value": data.get("start", "")},
                    {"title": "End",    "value": data.get("end", "")},
                    {"title": "Type",   "value": data.get("leave_type", "")},
                ],
            },
            {
                # Small grey note at the bottom.
                "type": "TextBlock",
                "text": "Your manager has been notified.",
                "isSubtle": True,
                "wrap": True,
            },
        ],
    }
