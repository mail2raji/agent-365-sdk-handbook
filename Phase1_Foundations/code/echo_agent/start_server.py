# start_server.py
"""Tiny aiohttp server that hosts an AgentApplication.

You will almost never modify this file. It exists so you can see the
plumbing once. From Phase 2 onward we just import it.

KID-FRIENDLY VERSION:
    This is the LEMONADE STAND. The agent (brain) makes the lemonade,
    but somebody has to set up the table on the sidewalk so customers
    can walk up and order. That's this file: it puts the table out,
    sticks up the "OPEN" sign, and listens for orders on port 3978.
"""
# `from __future__ import annotations` = "let me use new-style type hints
# (`list[int]`, `X | None`) on older Pythons."
from __future__ import annotations

# `os` lets us read computer settings (like environment variables — PORT, etc.).
import os
# `logging` = our diary again, same as in app.py.
import logging
# `aiohttp.web` = a tiny web server. Think of it as a one-table lemonade stand
# that can handle many customers at once because it's `async`.
from aiohttp import web
# `CloudAdapter` = the PHONE LINE between Teams/Emulator and our agent.
# It speaks the Bot Framework protocol so we don't have to.
from microsoft_agents.hosting.aiohttp import CloudAdapter
# We only need the TYPE here — we never `AgentApplication()` ourselves in this file.
from microsoft_agents.hosting.core import AgentApplication

# Our diary pen for this file.
logger = logging.getLogger(__name__)


def start_server(agent_app: AgentApplication, adapter: CloudAdapter | None = None) -> None:
    """Start an HTTP server hosting `agent_app` on port 3978.

    KID VERSION:
        Plug the brain (`agent_app`) into the phone (`adapter`),
        then open the lemonade stand window so customers can shout orders
        at http://localhost:3978/api/messages.
    """
    # If the caller didn't bring a phone, give them a default one.
    if adapter is None:
        adapter = CloudAdapter()

    # This little function runs for EVERY incoming message.
    # The phone (`adapter`) listens, decodes the message, then asks the
    # brain (`agent_app`) what to do.
    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, agent_app)

    # Build the web application and tell it: "POSTs to /api/messages go to `messages`".
    app = web.Application()
    app.router.add_post("/api/messages", messages)

    # Read the PORT env var if it's set; otherwise default to 3978
    # (the Bot Framework Emulator's favourite number).
    port = int(os.environ.get("PORT", 3978))
    logger.info(f"Listening on http://localhost:{port}/api/messages")
    # `web.run_app` BLOCKS here forever, taking orders until you Ctrl+C.
    web.run_app(app, host="localhost", port=port)
