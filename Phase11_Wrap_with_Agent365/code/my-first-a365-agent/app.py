"""
Phase 11 starter agent — "Hello, world!" with Agent 365 observability wired in.

This file is the FINAL version (after Section 9 of the lab). For the bare
pre-observability version, comment out the four blocks marked
`# A365 Observability — best-effort instrumentation (verify against official sample)`.
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from aiohttp import web

from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)

# A365 Observability — best-effort instrumentation (verify against official sample)
from microsoft.opentelemetry import use_microsoft_opentelemetry
from microsoft.opentelemetry.a365.core import BaggageBuilder
from microsoft.opentelemetry.a365.hosting.scope_helpers.populate_baggage import populate
from microsoft.opentelemetry.a365.hosting.token_cache_helpers import (
    AgenticTokenCache,
    AgenticTokenStruct,
)
from microsoft.opentelemetry.a365.runtime import get_observability_authentication_scope

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hello-a365")

AGENT_APP = AgentApplication(storage=MemoryStorage())


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "👋 Hi! I am your first Agent 365 agent. Say anything and I will echo it."
            )


@AGENT_APP.activity("message")
async def echo(context: TurnContext, state: TurnState):
    # A365 Observability — best-effort instrumentation (verify against official sample)
    # OBO auth mode: token exchange resolves to the signed-in user.
    # See: https://learn.microsoft.com/en-us/entra/agent-id/agent-on-behalf-of-oauth-flow
    token_cache = AgenticTokenCache()
    try:
        token_cache.register_observability(
            agent_id=context.activity.recipient.agentic_app_id,
            tenant_id=context.activity.recipient.tenant_id,
            token_generator=AgenticTokenStruct(
                authorization=None,
                turn_context=context,
            ),
            observability_scopes=get_observability_authentication_scope(),
        )
    except Exception as exc:  # observability must never break the agent
        log.warning("A365 observability token registration failed: %s", exc)

    # A365 Observability — best-effort instrumentation (verify against official sample)
    builder = BaggageBuilder()
    populate(builder, context)
    with builder.build():
        user_text = context.activity.text or ""
        await context.send_activity(f"You said: {user_text}")


def main() -> None:
    # A365 Observability — best-effort instrumentation (verify against official sample)
    use_microsoft_opentelemetry(
        service_name="my-first-a365-agent",
        enable_a365=True,
        a365_token_resolver=AgenticTokenCache().get_cached_token,
    )

    adapter = CloudAdapter()

    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, AGENT_APP)

    async def healthz(_req: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/healthz", healthz)
    port = int(os.environ.get("PORT", 3978))
    log.info("Listening on http://localhost:%s/api/messages", port)
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
