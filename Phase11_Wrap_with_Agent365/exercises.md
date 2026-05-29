# Phase 11 — Exercises

Stretch tasks once your lab agent is live. Difficulty increases top-to-bottom. ⭐ = beginner, ⭐⭐ = intermediate, ⭐⭐⭐ = advanced.

---

## ⭐ 1. Personalize the welcome

Edit `welcome()` in `app.py` to greet the user by name (hint: `context.activity.members_added[i].name`). Redeploy with `a365 deploy` and verify in Teams.

---

## ⭐ 2. Add a `/help` command

Add a second handler that responds to the exact text `/help` with a multi-line message listing what the agent can do.

```python
@AGENT_APP.message("/help")
async def help_cmd(context, state):
    await context.send_activity(
        "Commands:\n• /help — show this help\n• anything else — I echo it"
    )
```

Redeploy. Test in Teams.

---

## ⭐⭐ 3. Add a tool span

Add a fake "lookup" tool the user can trigger with `/time`. Wrap the call in an `ExecuteToolScope` so it appears in the Control Panel as a tool span.

Hints:
- Import `ExecuteToolScope` from `microsoft.opentelemetry.a365.core.scopes`.
- Open it *inside* the `with builder.build():` block so it nests under the `InvokeAgentScope`.

Verify the tool span appears in **Agent 365 Control Panel → your agent → Telemetry**.

---

## ⭐⭐ 4. Add a real LLM call

1. Set up an Azure OpenAI resource (Phase 5).
2. Add `openai>=1.0` to `requirements.txt`.
3. On every user message, call the LLM and return its reply.
4. Wrap the call in an `InferenceScope`. Provide `model`, `provider`, and `inputTokens`/`outputTokens` so the Control Panel can break costs down.

Verify the **InferenceScope** span shows up nested under **InvokeAgentScope** in the portal.

---

## ⭐⭐ 5. Write a custom Defender XDR detection

Build a KQL detection rule for one of the following risks:

- More than 50 turns from a single user in 5 minutes (likely abuse).
- Any agent reply containing the word `password`, `ssn`, or a 16-digit number (potential data leak).
- Any agent call from outside business hours (after-hours activity).

Save it as a **custom detection rule** in the Defender XDR portal.

---

## ⭐⭐⭐ 6. Switch from OBO to S2S

Refactor the agent so it runs as a **service-to-service (autonomous)** agent. You'll need to:

1. Re-run `a365 setup all --auth-mode S2S` (or follow the prompt during interactive setup).
2. Swap `AgenticTokenCache` (OBO) for the **token service** scaffold in [`references/python-observability.md`](https://github.com/microsoft/Agent365-devTools/blob/main/docs/agent365-guided-setup/references/python-observability.md) → S2S section.
3. Add `AGENT365_USE_S2S_ENDPOINT=true` to `.env`.
4. Provide `CallerDetails` with the Blueprint sponsor identity so traces show up in MAC portal.
5. Redeploy and confirm in Defender XDR that traces still arrive but `UserId` is now the **agent's** identity, not the user's.

---

## ⭐⭐⭐ 7. Add a CI/CD pipeline

Replace manual `a365 deploy` with a GitHub Actions workflow:

```yaml
name: deploy
on:
  push:
    branches: [main]
permissions:
  id-token: write
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      - run: dotnet tool install --global Microsoft.Agents.A365.DevTools.Cli --prerelease
      - run: a365 deploy --skip-confirm
```

Bonus: store `a365.generated.config.json` in the repo (it has no secrets) and gate `deploy` on a successful `pytest` run.

---

## ⭐⭐⭐ 8. Multi-agent A2A

Build a *second* agent in the same tenant that **calls** the first one (Agent-to-Agent). Confirm that:

- The first agent's `InvokeAgentScope` is created inside the second agent's `ExecuteToolScope` (i.e. distributed tracing works end-to-end).
- The **AgentActivity** Defender XDR table shows both turns with matching `ConversationId`/`TraceId`.

Hints: Phase 9 covers A2A patterns. The runtime uses W3C traceparent headers automatically.
