# start_server.py — Phase 10 capstone version (with /healthz probe)
#
# KID-FRIENDLY VERSION:
#     Same lemonade stand as the earlier phases, with ONE extra window:
#     `/healthz` returns `{"ok": true}`. Container Apps / Kubernetes call
#     this URL to ask "are you alive?" — if it stops answering, they
#     restart the agent automatically.

from __future__ import annotations
import os, logging
from aiohttp import web
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import AgentApplication

logger = logging.getLogger(__name__)


def start_server(agent_app: AgentApplication, adapter: CloudAdapter | None = None) -> None:
    if adapter is None:
        adapter = CloudAdapter()

    # Main chat endpoint — same as every other phase.
    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, agent_app)

    # Health probe. Returns a tiny JSON "I'm alive" so the platform knows
    # to keep us running. NEVER touch external services here — it must be
    # cheap and instant.
    async def healthz(_req: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/api/messages", messages)   # chats come in here
    app.router.add_get("/healthz", healthz)          # platform pings here
    port = int(os.environ.get("PORT", 3978))
    logger.info(f"Listening on http://localhost:{port}/api/messages")
    web.run_app(app, host="localhost", port=port)
