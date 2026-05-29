# 🧩 Phase 8 — Exercises

## Exercise 1 — Name the SDKs

What's the difference between **Microsoft 365 Agents SDK** and **Microsoft Agent 365 SDK**?

<details><summary>Answer</summary>

- **Microsoft 365 Agents SDK** = foundation (handlers, state, channels). Packages: `microsoft-agents-hosting-*`, `microsoft-agents-activity`.
- **Microsoft Agent 365 SDK** = enterprise layer on top (identity, governed MCP, notifications, observability). Packages: `microsoft-agents-a365-*`. Pre-release.

</details>

---

## Exercise 2 — Install command

Write the command to install the four A365 packages using `uv`.

<details><summary>Answer</summary>

```powershell
uv pip install --prerelease=allow `
    microsoft-agents-a365-identity `
    microsoft-agents-a365-mcp `
    microsoft-agents-a365-notifications `
    microsoft-agents-a365-observability-otlp
```

</details>

---

## Exercise 3 — Why governed identity?

What does Agent 365 identity give you beyond a plain Bot App Registration?

<details><summary>Answer</summary>

Cryptographic provability, metadata (owner, scopes, lifecycle), tenant-policy enforcement, and auditability in Purview. Each agent action is attributable to that identity.

</details>

---

## Exercise 4 — Discover vs hard-code

Why is discovering MCP tools from the catalog better than hard-coding URLs?

<details><summary>Answer</summary>

- Admins govern the catalog (revoke, rate-limit, audit centrally).
- No code changes when endpoints move.
- Per-tenant config — same code works across customers.
- The catalog enforces scopes, so a bug can't accidentally call a tool the agent lacks permission for.

</details>

---

## Exercise 5 — Register a tool

What CLI command registers an MCP tool manifest?

<details><summary>Answer</summary>

```powershell
a365 mcp register --manifest mcp_tool.yaml
```

</details>

---

## Exercise 6 — Same tool loop

How much of the Phase 6 tool loop changes when you switch from local tools to `McpToolset`?

<details><summary>Answer</summary>

Almost none. You replace `TOOLS` with `toolset.openai_tools()` and replace your `call_tool(...)` dispatch with `await toolset.invoke(name, args)`. The loop structure is identical.

</details>

---

## Exercise 7 — One-line OTel

Show the single function call that enables OpenTelemetry traces in the agent.

<details><summary>Answer</summary>

```python
configure_otel(service_name="helpdesk-agent",
               endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"])
```

</details>

---

## Exercise 8 — App Insights wiring

Which env var do you set so OTel data lands in Application Insights?

<details><summary>Answer</summary>

`AZURE_APP_INSIGHTS_CONNECTION_STRING` (and / or `OTEL_EXPORTER_OTLP_ENDPOINT` for direct OTLP). The A365 observability package reads both.

</details>

---

## Exercise 9 — Notification audience

How would you notify *every member* of a Teams team via A365 notifications?

<details><summary>Answer</summary>

```python
await notifier.send(
    Notification(
        template_id="team-alert-v1",
        audience={"team_id": team_id},
        data={...},
    )
)
```

The exact audience shape depends on the preview version — check `a365 notifications send --help`.

</details>

---

## Exercise 10 — Where templates live

Why are notification templates stored server-side, not in your code?

<details><summary>Answer</summary>

So your security/governance team can review and approve content, manage versions, enforce branding and accessibility, and update templates without redeploying the agent.

</details>

---

## Exercise 11 — Identity-bound MCP

Why does `McpToolset.from_catalog(identity)` take the **identity** parameter?

<details><summary>Answer</summary>

The catalog returns only tools that *this identity* is allowed to call (per admin policy). Token issuance and audit trail are also bound to the identity, not the user.

</details>

---

## Exercise 12 — Pre-release safety

Why wrap A365 imports in `try/except` during learning?

<details><summary>Answer</summary>

Pre-release packages may not be installed yet (especially when sharing the workspace with people on a different schedule). The guard lets the file load and the agent still respond — degrading to local tools — instead of crashing on import.

</details>

---

## Exercise 13 — Production-ready order

What's a sensible build order for a new enterprise agent?

<details><summary>Answer</summary>

1. Foundation skeleton (Phase 1–2): handlers + state.
2. LLM (Phase 5).
3. Local tools (Phase 6) — prove the loop.
4. Add A365 identity and switch to governed MCP.
5. Add A365 OTel.
6. Add A365 notifications.
7. Deploy (Phase 9) and monitor.

</details>

---

## Exercise 14 — Bonus: trace a turn

You see latency spikes. Which OTel signals help, and what would you look at?

<details><summary>Answer</summary>

- **Traces**: per-turn span tree — find the slow child span (LLM, MCP, Graph, storage).
- **Metrics**: LLM token counts and p95 latency over time.
- **Logs**: warnings/errors with the trace id, to correlate.

App Insights' **Application Map** visualizes this with one click.

</details>

---

## Exercise 15 — Bonus: governance story

Pitch in 3 sentences why an enterprise should use Agent 365 instead of just the foundation SDK.

<details><summary>Answer</summary>

> The foundation SDK lets you ship agents. Agent 365 lets you ship **trustworthy** agents: every agent has a provable identity, every tool call goes through an approved catalog, every notification is templated and audited, and every turn is observable end-to-end in OpenTelemetry. That's the difference between a demo and a production-supported system in a regulated enterprise.

</details>

---

✅ Next → **[Phase 9 — Testing & Deployment](../Phase9_Testing_and_Deployment/README.md)**.
