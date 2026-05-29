"""Governed Helpdesk Agent — Phase 8.

Demonstrates layering A365 identity + governed MCP + OTel on top of the foundation SDK.

A365 imports are wrapped in try/except so the file loads even without the
pre-release packages. When a piece is missing, the agent degrades to local-only
behavior (still useful as a learning exercise).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)

from start_server import start_server

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("governed-helpdesk")


# ---------- A365 identity ----------
IDENTITY = None
try:
    from microsoft_agents_a365.identity import AgentIdentity  # type: ignore

    IDENTITY = AgentIdentity.from_env()
    log.info("A365 identity loaded: %s", IDENTITY)
except Exception as e:  # noqa: BLE001
    log.warning("A365 identity unavailable, using foundation only: %s", e)


# ---------- A365 OTel observability ----------
try:
    from microsoft_agents_a365.observability.otlp import configure_otel  # type: ignore

    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        configure_otel(
            service_name="helpdesk-agent",
            endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"],
        )
        log.info("OTel exporter configured.")
except Exception as e:  # noqa: BLE001
    log.warning("A365 OTel not available: %s", e)


# ---------- A365 MCP toolset ----------
TOOLSET = None
try:
    from microsoft_agents_a365.mcp import McpToolset  # type: ignore

    if IDENTITY is not None:
        TOOLSET = None  # populated lazily on first turn (needs await)
except Exception as e:  # noqa: BLE001
    log.warning("A365 MCP not available: %s", e)


# Fallback local tools (so the agent still works without governed MCP)
LOCAL_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "lookup_ticket",
            "description": "Look up an IT support ticket by ID.",
            "parameters": {
                "type": "object",
                "properties": {"ticket_id": {"type": "string"}},
                "required": ["ticket_id"],
            },
        },
    },
]


async def call_local_tool(name: str, args: dict) -> str:
    if name == "lookup_ticket":
        return f"Ticket {args['ticket_id']}: Open. Priority P2. Assigned to Helpdesk-L2."
    return f"Unknown tool {name}"


SYSTEM_PROMPT = (
    "You are an enterprise IT helpdesk agent. "
    "Use governed tools whenever they help. Be concise. "
    "If you can't find an answer, ask the user to open a ticket."
)


def _client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


async def _get_toolset_and_tools():
    """Resolve the active toolset + tool schemas.

    Prefers governed MCP if available. Falls back to LOCAL_TOOLS.
    """
    global TOOLSET
    if IDENTITY is not None:
        try:
            from microsoft_agents_a365.mcp import McpToolset  # type: ignore

            if TOOLSET is None:
                TOOLSET = await McpToolset.from_catalog(IDENTITY)
            return TOOLSET, TOOLSET.openai_tools()
        except Exception as e:  # noqa: BLE001
            log.warning("Falling back to local tools: %s", e)
    return None, LOCAL_TOOLS


async def chat_with_tools(history: list[dict], user_msg: str) -> str:
    history.append({"role": "user", "content": user_msg})
    toolset, tools = await _get_toolset_and_tools()
    for _ in range(5):
        resp = await _client().chat.completions.create(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = resp.choices[0].message
        history.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return msg.content or ""

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            name = call.function.name
            log.info(f"tool: {name}({args})")
            if toolset is not None:
                result = await toolset.invoke(name, args)
            else:
                result = await call_local_tool(name, args)
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                }
            )
    return "Sorry, I'm stuck. Please open a ticket."


AGENT_APP = AgentApplication(storage=MemoryStorage(), identity=IDENTITY)


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "🏢 Governed helpdesk agent online. Ask me about a ticket "
                "(e.g. 'Status of ticket INC1234?')."
            )


@AGENT_APP.message("reset")
async def reset(context: TurnContext, state: TurnState):
    state.conversation["history"] = []
    await context.send_activity("🧹 History cleared.")


@AGENT_APP.activity("message")
async def chat(context: TurnContext, state: TurnState):
    history = state.conversation.get("history", [])
    try:
        reply = await chat_with_tools(history, context.activity.text or "")
    except Exception as e:  # noqa: BLE001
        log.exception("LLM/tool failure")
        await context.send_activity(f"⚠️ {e}")
        return
    state.conversation["history"] = history
    await context.send_activity(reply)


if __name__ == "__main__":
    start_server(AGENT_APP, None)
