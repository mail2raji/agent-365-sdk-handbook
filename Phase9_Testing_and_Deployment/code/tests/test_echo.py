"""Sample unit tests using TestAdapter.

Run with: pytest -q
"""
from __future__ import annotations

import pytest

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TestAdapter,
    TurnContext,
    TurnState,
)


@pytest.mark.asyncio
async def test_echo_replies() -> None:
    app = AgentApplication(storage=MemoryStorage())

    @app.activity("message")
    async def on_msg(context: TurnContext, state: TurnState):
        await context.send_activity(f"You said: {context.activity.text}")

    adapter = TestAdapter()
    await adapter.process_activity_with_message("hi", app)
    reply = adapter.get_next_reply()
    assert reply.text == "You said: hi"


@pytest.mark.asyncio
async def test_command_router() -> None:
    app = AgentApplication(storage=MemoryStorage())

    @app.message("help")
    async def help_(context: TurnContext, state: TurnState):
        await context.send_activity("commands: help, hi")

    @app.message("hi")
    async def hi(context: TurnContext, state: TurnState):
        await context.send_activity("hello!")

    adapter = TestAdapter()

    await adapter.process_activity_with_message("hi", app)
    assert adapter.get_next_reply().text == "hello!"

    await adapter.process_activity_with_message("help", app)
    assert adapter.get_next_reply().text == "commands: help, hi"


@pytest.mark.asyncio
async def test_state_round_trip() -> None:
    app = AgentApplication(storage=MemoryStorage())

    @app.activity("message")
    async def incr(context: TurnContext, state: TurnState):
        n = state.conversation.get("n", 0) + 1
        state.conversation["n"] = n
        await context.send_activity(f"count={n}")

    adapter = TestAdapter()
    await adapter.process_activity_with_message("x", app)
    await adapter.process_activity_with_message("x", app)
    await adapter.process_activity_with_message("x", app)

    replies = [adapter.get_next_reply().text for _ in range(3)]
    assert replies == ["count=1", "count=2", "count=3"]
