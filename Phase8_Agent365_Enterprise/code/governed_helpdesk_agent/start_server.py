# start_server.py — reusable "lemonade-stand" plumbing
#
# KID-FRIENDLY VERSION:
#     This is the LEMONADE STAND that sets up the table and shouts "OPEN!"
#     so customers (Teams, the Bot Framework Emulator, our PowerShell helper)
#     can walk up and order. The brain (`agent_app`) makes the lemonade.
#     This file just runs the stand. You'll see this file repeated in every
#     phase — that's on purpose, so you can read each phase by itself.

# Let me use new-style type hints like `CloudAdapter | None` even on
# older Python versions. Without this line, `X | None` would error.
from __future__ import annotations
# `os` = read computer settings (env vars). `logging` = our diary.
import os, logging
# `aiohttp.web` = a tiny async web server (the lemonade-stand table).
from aiohttp import web
# `CloudAdapter` = the PHONE LINE between Bot Framework callers and our brain.
# It speaks the Bot Framework protocol so we don't have to.
from microsoft_agents.hosting.aiohttp import CloudAdapter
# Imported only as a TYPE so editors can autocomplete — we never call
# `AgentApplication()` here. The caller passes in a ready-made brain.
from microsoft_agents.hosting.core import AgentApplication

logger = logging.getLogger(__name__)   # diary pen labelled with this file's name


def start_server(agent_app: AgentApplication, adapter: CloudAdapter | None = None) -> None:
    """Start an HTTP server hosting `agent_app` on port 3978.

    KID VERSION:
        Plug the brain (`agent_app`) into the phone (`adapter`),
        then open the stand at http://localhost:3978/api/messages.
    """
    # If the caller didn't bring a phone, give them a default one.
    if adapter is None:
        adapter = CloudAdapter()

    # This little function runs for EVERY POST to /api/messages.
    # The phone (adapter) decodes the request, asks the brain (agent_app)
    # what to say, then sends the response back.
    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, agent_app)

    # Build the web app and wire up the one route we care about.
    app = web.Application()
    app.router.add_post("/api/messages", messages)
    # PORT env var wins; otherwise default to 3978 (Bot Framework Emulator's favourite).
    port = int(os.environ.get("PORT", 3978))
    logger.info(f"Listening on http://localhost:{port}/api/messages")
    # BLOCKS forever, taking orders until you press Ctrl+C.
    web.run_app(app, host="localhost", port=port)
