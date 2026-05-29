"""Adaptive Card builders for the Leave-Request Agent."""
from __future__ import annotations


def build_leave_request_card() -> dict:
    """Return the JSON dict for the leave-request input card."""
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "size": "Large",
                "weight": "Bolder",
                "text": "📝 Request Time Off",
            },
            {
                "type": "Input.Text",
                "id": "reason",
                "label": "Reason",
                "placeholder": "Why are you taking leave?",
                "isRequired": True,
                "errorMessage": "Please provide a reason.",
            },
            {
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
                "type": "Input.ChoiceSet",
                "id": "leave_type",
                "label": "Type",
                "style": "compact",
                "value": "vacation",
                "choices": [
                    {"title": "Vacation", "value": "vacation"},
                    {"title": "Sick", "value": "sick"},
                    {"title": "Personal", "value": "personal"},
                ],
            },
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Submit",
                "data": {"action": "submit_leave"},
            }
        ],
    }


def build_confirmation_card(request_id: str, data: dict) -> dict:
    """Confirmation card shown after submission."""
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
                "type": "FactSet",
                "facts": [
                    {"title": "Reason", "value": data.get("reason", "")},
                    {"title": "Start", "value": data.get("start", "")},
                    {"title": "End", "value": data.get("end", "")},
                    {"title": "Type", "value": data.get("leave_type", "")},
                ],
            },
            {
                "type": "TextBlock",
                "text": "Your manager has been notified.",
                "isSubtle": True,
                "wrap": True,
            },
        ],
    }
