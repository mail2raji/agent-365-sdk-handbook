"""Sample unit tests using TestAdapter.

Run with: pytest -q

KID-FRIENDLY VERSION:
    These tests are like CRASH-TEST DUMMIES for our agent. We don't
    spin up Teams or HTTP \u2014 we just hand a fake message to the brain
    using `TestAdapter`, then check the reply. Super fast, totally
    offline. Run them every time you change the agent so nothing breaks.
"""
from __future__ import annotations

# `pytest` = the test runner. The `@pytest.mark.asyncio` sticker tells
# pytest \"this test is async, please await it\".
import pytest

from microsoft_agents.hosting.core import (
    AgentApplication,   # the BRAIN we want to test
    MemoryStorage,      # SHOEBOX for sticky notes
    TestAdapter,        # FAKE phone line \u2014 no real HTTP, no Teams
    TurnContext,        # \"this chat moment\"
    TurnState,          # the sticky NOTE for this chat
)


@pytest.mark.asyncio
async def test_echo_replies() -> None:
    # 1. Build a tiny throw-away agent that echoes whatever you say.
    app = AgentApplication(storage=MemoryStorage())

    @app.activity("message")
    async def on_msg(context: TurnContext, state: TurnState):
        await context.send_activity(f"You said: {context.activity.text}")

    # 2. Make a fake phone line and pretend the user typed \"hi\".
    adapter = TestAdapter()
    await adapter.process_activity_with_message("hi", app)
    # 3. Pull the next reply from the fake outbox and check it.
    reply = adapter.get_next_reply()
    assert reply.text == "You said: hi"


@pytest.mark.asyncio
async def test_command_router() -> None:
    # Show that we can register TWO handlers and the right one fires
    # depending on the message text.
    app = AgentApplication(storage=MemoryStorage())

    @app.message("help")
    async def help_(context: TurnContext, state: TurnState):
        await context.send_activity("commands: help, hi")

    @app.message("hi")
    async def hi(context: TurnContext, state: TurnState):
        await context.send_activity("hello!")

    adapter = TestAdapter()

    # Send \"hi\" \u2192 expect \"hello!\".
    await adapter.process_activity_with_message("hi", app)
    assert adapter.get_next_reply().text == "hello!"

    # Send \"help\" \u2192 expect the menu.
    await adapter.process_activity_with_message("help", app)
    assert adapter.get_next_reply().text == "commands: help, hi"


@pytest.mark.asyncio
async def test_state_round_trip() -> None:
    # Prove that the sticky note (`state.conversation`) survives across
    # turns within the same fake conversation.
    app = AgentApplication(storage=MemoryStorage())

    @app.activity("message")
    async def incr(context: TurnContext, state: TurnState):
        # Read \u2192 +1 \u2192 write back.
        n = state.conversation.get("n", 0) + 1
        state.conversation["n"] = n
        await context.send_activity(f"count={n}")

    adapter = TestAdapter()
    # Three messages \u2192 three counts.
    await adapter.process_activity_with_message("x", app)
    await adapter.process_activity_with_message("x", app)
    await adapter.process_activity_with_message("x", app)

    # Pull all three replies in order and check they count up.
    replies = [adapter.get_next_reply().text for _ in range(3)]
    assert replies == ["count=1", "count=2", "count=3"]
