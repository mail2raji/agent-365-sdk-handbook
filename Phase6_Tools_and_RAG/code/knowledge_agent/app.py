"""IT Knowledge Agent — Phase 6.

Demonstrates tools + RAG.
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
from rag import VectorStore, build_default_store

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("knowledge-agent")

AGENT_APP = AgentApplication(storage=MemoryStorage())
STORE: VectorStore | None = None  # lazily built on first message


# ---------- Tool implementations ----------
def get_weather(city: str) -> str:
    # mock — replace with a real API call
    return f"It's 22°C and sunny in {city}."


def reset_password(user_email: str) -> str:
    return f"Done. A temporary password was emailed to {user_email}."


async def lookup_policy(question: str) -> str:
    assert STORE is not None
    hits = await STORE.search(question, k=3)
    if not hits:
        return "No matching policy found."
    return "\n---\n".join(f"[{d.title}] {d.text}" for d in hits)


# ---------- Tool schemas ----------
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city. Use when user asks about weather.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_password",
            "description": "Reset a user's password and email them a temporary one.",
            "parameters": {
                "type": "object",
                "properties": {"user_email": {"type": "string"}},
                "required": ["user_email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_policy",
            "description": (
                "Search the company knowledge base for policies and IT guidance. "
                "Use when the user asks about company rules, password policy, VPN, MFA, travel, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
]


SYSTEM_PROMPT = (
    "You are an IT support assistant for Contoso employees. "
    "Use tools whenever they can help. "
    "When you answer policy questions, quote the relevant snippet from `lookup_policy`. "
    "Keep replies short and friendly."
)


def _client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


async def call_tool(name: str, args: dict) -> str:
    if name == "get_weather":
        return get_weather(**args)
    if name == "reset_password":
        return reset_password(**args)
    if name == "lookup_policy":
        return await lookup_policy(**args)
    return f"Unknown tool: {name}"


async def chat_with_tools(history: list[dict], user_msg: str) -> str:
    history.append({"role": "user", "content": user_msg})
    for _ in range(5):  # safety cap
        resp = await _client().chat.completions.create(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = resp.choices[0].message
        history.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return msg.content or ""

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            log.info(f"tool: {call.function.name}({args})")
            result = await call_tool(call.function.name, args)
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )
    return "Sorry, I'm stuck in a tool loop. Please rephrase."


# ---------- Agent handlers ----------
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    global STORE
    if STORE is None:
        log.info("Building vector store...")
        STORE = await build_default_store()
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "🤖 Hi! I'm your IT helper. Try:\n"
                "• 'What's our password policy?'\n"
                "• 'Reset my password for jane@contoso.com.'\n"
                "• 'What's the weather in Berlin?'"
            )


@AGENT_APP.message("reset")
async def reset(context: TurnContext, state: TurnState):
    state.conversation["history"] = []
    await context.send_activity("🧹 History cleared.")


@AGENT_APP.activity("message")
async def chat(context: TurnContext, state: TurnState):
    global STORE
    if STORE is None:
        STORE = await build_default_store()
    history = state.conversation.get("history", [])
    try:
        reply = await chat_with_tools(history, context.activity.text or "")
    except Exception as e:
        log.exception("LLM/tool failure")
        await context.send_activity(f"⚠️ {e}")
        return
    state.conversation["history"] = history
    await context.send_activity(reply)


if __name__ == "__main__":
    start_server(AGENT_APP, None)
