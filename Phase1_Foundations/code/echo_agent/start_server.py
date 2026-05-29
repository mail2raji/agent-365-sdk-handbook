# start_server.py
"""Tiny aiohttp server that hosts an AgentApplication.

You will almost never modify this file. It exists so you can see the
plumbing once. From Phase 2 onward we just import it.
"""
from __future__ import annotations

import os
import logging
from aiohttp import web
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import AgentApplication

logger = logging.getLogger(__name__)


def start_server(agent_app: AgentApplication, adapter: CloudAdapter | None = None) -> None:
    """Start an HTTP server hosting `agent_app` on port 3978."""
    if adapter is None:
        adapter = CloudAdapter()

    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, agent_app)

    app = web.Application()
    app.router.add_post("/api/messages", messages)

    port = int(os.environ.get("PORT", 3978))
    logger.info(f"Listening on http://localhost:{port}/api/messages")
    web.run_app(app, host="localhost", port=port)
