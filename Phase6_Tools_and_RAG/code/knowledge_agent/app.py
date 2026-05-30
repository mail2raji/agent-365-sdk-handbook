"""IT Knowledge Agent — Phase 6.

Demonstrates tools + RAG.

KID-FRIENDLY VERSION:
    Two new super-powers in this phase:
      1. TOOLS — little Python functions the LLM is allowed to call.
         Like giving the smart robot a hammer and a screwdriver.
         When the LLM thinks "I need the weather", it says so, we run
         the tool, hand the answer back, and the LLM weaves it into the
         reply.
      2. RAG (Retrieval-Augmented Generation) — a tiny library of company
         documents (the "knowledge base"). When the user asks a policy
         question, we look up the closest snippets and feed them to the LLM
         so it answers with facts, not guesses.
"""
from __future__ import annotations

import json                 # turn dicts ↔ JSON strings (tool args come as JSON)
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
# Our tiny in-memory vector store + a builder that seeds it with docs.
from rag import VectorStore, build_default_store

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("knowledge-agent")

AGENT_APP = AgentApplication(storage=MemoryStorage())
# Global STORE — built ONCE on the first message (lazy init), reused after.
# `None` means "not built yet".
STORE: VectorStore | None = None  # lazily built on first message


# ---------- Tool implementations ----------
# Plain Python functions. The LLM never calls these directly; the agent
# calls them when the LLM ASKS for a tool by name.
def get_weather(city: str) -> str:
    # MOCK — in a real agent you'd call OpenWeather or similar.
    return f"It's 22°C and sunny in {city}."


def reset_password(user_email: str) -> str:
    return f"Done. A temporary password was emailed to {user_email}."


async def lookup_policy(question: str) -> str:
    # `assert` = double-check that STORE has been built. If not, crash early.
    assert STORE is not None
    hits = await STORE.search(question, k=3)        # top 3 closest docs
    if not hits:
        return "No matching policy found."
    # Stitch the 3 snippets together with a divider so the LLM can quote them.
    return "\n---\n".join(f"[{d.title}] {d.text}" for d in hits)


# ---------- Tool schemas ----------
# This is the MENU we show the LLM: name + description + what arguments
# each tool needs. The LLM uses the descriptions to decide WHEN to call.
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


# The SYSTEM prompt tells the LLM how to behave for EVERY user message.
SYSTEM_PROMPT = (
    "You are an IT support assistant for Contoso employees. "
    "Use tools whenever they can help. "
    "When you answer policy questions, quote the relevant snippet from `lookup_policy`. "
    "Keep replies short and friendly."
)


def _client() -> AsyncAzureOpenAI:
    # Build a fresh OpenAI client per call. Same pattern as Phase 5.
    return AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


async def call_tool(name: str, args: dict) -> str:
    # DISPATCH table in if-form. The LLM gives us the tool name; we route it.
    if name == "get_weather":
        return get_weather(**args)
    if name == "reset_password":
        return reset_password(**args)
    if name == "lookup_policy":
        return await lookup_policy(**args)
    return f"Unknown tool: {name}"


async def chat_with_tools(history: list[dict], user_msg: str) -> str:
    # 1. Add the new user message to history.
    history.append({"role": "user", "content": user_msg})
    # 2. Loop up to 5 times. Each loop is: ask the LLM → if it wants tools,
    #    run them, append results, ask again. The cap prevents infinite loops.
    for _ in range(5):  # safety cap
        resp = await _client().chat.completions.create(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            tools=TOOLS,             # show the LLM the menu
            tool_choice="auto",      # let the LLM decide if/which to call
            temperature=0.2,         # low = focused, factual answers
        )
        msg = resp.choices[0].message
        # Save the LLM's message (could include tool_calls) to history.
        history.append(msg.model_dump(exclude_none=True))
        # If the LLM didn't ask for tools, this IS the final answer.
        if not msg.tool_calls:
            return msg.content or ""

        # The LLM asked for one or more tool calls. Run each one.
        for call in msg.tool_calls:
            # Tool arguments arrive as a JSON STRING — parse to a dict.
            args = json.loads(call.function.arguments or "{}")
            log.info(f"tool: {call.function.name}({args})")
            result = await call_tool(call.function.name, args)
            # Hand the result back to the LLM as a `tool` role message,
            # tagged with the original tool_call_id so it knows which is which.
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )
    # Safety net — if we burned all 5 loops, give up gracefully.
    return "Sorry, I'm stuck in a tool loop. Please rephrase."


# ---------- Agent handlers ----------
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    global STORE
    # Build the vector store on the first welcome — cheaper than blocking startup.
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
    # Safety net: if welcome never fired (rare), build the store now.
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
