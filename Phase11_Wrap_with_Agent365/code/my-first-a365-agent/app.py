"""
Phase 11 starter agent — "Hello, world!" with Agent 365 observability wired in.

This file is the FINAL version (after Section 9 of the lab). For the bare
pre-observability version, comment out the four blocks marked
`# A365 Observability — best-effort instrumentation (verify against official sample)`.

KID-FRIENDLY VERSION:
    A tiny PARROT that echoes whatever you say — but it has an
    enterprise BADGE. Every chat is wrapped with OpenTelemetry "luggage
    tags" (baggage) so the platform can prove WHICH agent + WHICH tenant
    produced each log line. Same parrot, way fancier paper trail.
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv              # read .env settings
from aiohttp import web                     # the lemonade STAND

from microsoft_agents.hosting.aiohttp import CloudAdapter          # PHONE LINE
from microsoft_agents.hosting.core import (
    AgentApplication,   # the BRAIN
    MemoryStorage,      # SHOEBOX (forgets on restart)
    TurnContext,        # "this chat moment"
    TurnState,          # sticky NOTE
)

# A365 Observability — best-effort instrumentation (verify against official sample)
# These imports give us 3 superpowers:
#   1. `use_microsoft_opentelemetry` \u2014 turn on OTel exporters in one call.
#   2. `BaggageBuilder` / `populate` \u2014 attach luggage tags (agent id,
#      tenant id, conversation id) to every span this turn creates.
#   3. `AgenticTokenCache` \u2014 grabs an OBO (on-behalf-of) token so the
#      OTel exporter can prove WHO it is when sending telemetry.
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

# One global BRAIN with an in-memory SHOEBOX. Production = swap to BlobStorage.
AGENT_APP = AgentApplication(storage=MemoryStorage())


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    # When a new person joins, wave hello \u2014 but only to the human, not to us.
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "\ud83d\udc4b Hi! I am your first Agent 365 agent. Say anything and I will echo it."
            )


@AGENT_APP.activity("message")
async def echo(context: TurnContext, state: TurnState):
    # A365 Observability — best-effort instrumentation (verify against official sample)
    # STEP 1 — register a BADGE for telemetry.
    # OBO auth mode: token exchange resolves to the signed-in user.
    # See: https://learn.microsoft.com/en-us/entra/agent-id/agent-on-behalf-of-oauth-flow
    token_cache = AgenticTokenCache()
    try:
        token_cache.register_observability(
            agent_id=context.activity.recipient.agentic_app_id,      # WHO is this agent
            tenant_id=context.activity.recipient.tenant_id,          # WHICH org
            token_generator=AgenticTokenStruct(
                authorization=None,
                turn_context=context,
            ),
            observability_scopes=get_observability_authentication_scope(),
        )
    except Exception as exc:  # observability must never break the agent
        # Telemetry is nice-to-have. If it fails, log a warning and keep going.
        log.warning("A365 observability token registration failed: %s", exc)

    # A365 Observability — best-effort instrumentation (verify against official sample)
    # STEP 2 — attach LUGGAGE TAGS. Everything inside the `with` block
    # produces OTel spans that carry agent_id / tenant_id / conversation_id
    # automatically, so an admin can filter logs by exactly this turn.
    builder = BaggageBuilder()
    populate(builder, context)
    with builder.build():
        user_text = context.activity.text or ""
        # The actual parrot \u2014 echo what you heard.
        await context.send_activity(f"You said: {user_text}")


def main() -> None:
    # A365 Observability — best-effort instrumentation (verify against official sample)
    # Turn on OpenTelemetry BEFORE we start serving traffic so the first
    # request is already captured. `service_name` shows up in App Insights.
    use_microsoft_opentelemetry(
        service_name="my-first-a365-agent",
        enable_a365=True,
        a365_token_resolver=AgenticTokenCache().get_cached_token,
    )

    adapter = CloudAdapter()      # PHONE LINE that translates HTTP \u2194 Activity

    # Main chat door.
    async def messages(req: web.Request) -> web.Response:
        return await adapter.process(req, AGENT_APP)

    # \"Are you alive?\" door for the platform.
    async def healthz(_req: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/api/messages", messages)   # incoming chats
    app.router.add_get("/healthz", healthz)          # liveness probe
    port = int(os.environ.get("PORT", 3978))
    log.info("Listening on http://localhost:%s/api/messages", port)
    # `host="0.0.0.0"` = listen on every network card (needed in containers).
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
