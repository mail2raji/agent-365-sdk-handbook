from __future__ import annotations
import os, logging
from aiohttp import web
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import AgentApplication

logger = logging.getLogger(__name__)


def start_server(agent_app: AgentApplication, adapter: CloudAdapter | None = None) -> None:
    if adapter is None:
        adapter = CloudAdapter()

    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, agent_app)

    async def healthz(_req: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/healthz", healthz)
    port = int(os.environ.get("PORT", 3978))
    logger.info(f"Listening on http://localhost:{port}/api/messages")
    web.run_app(app, host="localhost", port=port)
