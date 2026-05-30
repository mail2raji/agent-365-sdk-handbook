# 🧪 Phase 11 — Hands-On Lab: Wrap Your Agent with Agent 365

> The Phase 11 README **is** the long-form lab. This file gives you a tighter, milestone-checklist version with extra **practice exercises** to make sure each concept sticks. Read the README first; come back here to verify each milestone and stretch your understanding.

---

## 🎯 What you'll do today

Take a brand-new "hello world" agent built with the **Microsoft 365 Agents SDK** and wrap it with the **Microsoft Agent 365 SDK** so it:

- Has a tenant **agent identity**.
- Is **published** in the M365 Admin Center → Agents.
- Streams **OpenTelemetry traces** into the Agent 365 control panel.
- Appears in **Microsoft Defender XDR → Advanced Hunting**.

⏱️ **About 2 hours** end-to-end (most of which is provisioning).

---

## ✅ Before you start

- [ ] You've followed [the Phase 11 README](README.md) at least once and understand the flow.
- [ ] Prereqs from the README are all green: PS7, .NET 8, Azure CLI, Python 3.10/3.11, an Azure subscription, an M365 tenant in the **Frontier preview**, and at least **Agent ID Developer** role in that tenant.
- [ ] You have the agent code at [`code/my-first-a365-agent/`](https://github.com/mail2raji/agent-365-sdk-handbook/blob/main/Phase11_Wrap_with_Agent365/code/my-first-a365-agent) (or you built it from scratch in the README).

---

## 🗺️ Lab roadmap (matches the README milestones)

```
Lab 1 → Build & test the bare agent locally
Lab 2 → Install Agent 365 CLI + dry-run `setup all`
Lab 3 → Real `setup all`
Lab 4 → Publish + Deploy
Lab 5 → Teams blueprint config + first chat
Lab 6 → Add observability
Lab 7 → Validate in Admin Center, Control Panel, Defender XDR
Lab 8 → Cleanup
```

---

## Lab 1 — Bare agent locally (~20 min)

Follow [README §1](README.md#1️⃣-build-the-tiny-agent-10-minutes). Then verify:

### ✅ Checkpoint 1
- [ ] `python app.py` prints `Listening on http://localhost:3978/api/messages`.
- [ ] In the **Microsoft 365 Agents Playground** VS Code extension, the message `hello` returns `You said: hello`.
- [ ] You can hit `Ctrl+C` to stop.

### 🧠 Practice exercise
Without restarting the agent, add a second handler that responds to the word `time` with the current time:

```python
import datetime
@AGENT_APP.message("time")
async def show_time(context, state):
    await context.send_activity(f"⏰ {datetime.datetime.now():%H:%M:%S}")
```

Restart, test, confirm. **Make sure** `hello` still echoes — `@app.message("time")` is matched before the catch-all `@app.activity("message")` handler.

---

## Lab 2 — CLI + dry-run (~10 min)

Follow [README §2 and §3](README.md#2️⃣-install-the-agent-365-cli-5-minutes). Then run a dry-run:

```powershell
a365 setup all --agent-name <your-initials>-first-agent --dry-run
```

### ✅ Checkpoint 2
- [ ] `dotnet --version` ≥ 8.x.
- [ ] `a365 -h` shows `setup`, `publish`, `deploy`, `cleanup`.
- [ ] `az account show` displays the **correct** tenant.
- [ ] Dry-run prints a **resource preview table** with the planned resource group, web app, blueprint, and identity.
- [ ] No resources were actually created (confirm in the Azure portal).

### 🧠 Practice exercise
Re-run the dry-run with `--location eastus2` (or another region you have quota in). Compare the planned resource group name. **Why does the location affect the name?** (It usually doesn't — but pick a region close to you for lower latency.)

---

## Lab 3 — Real `setup all` (~20 min)

```powershell
a365 setup all --agent-name <your-initials>-first-agent
```

While it runs, watch the numbered steps. Capture the **Setup Summary** table at the end.

### ✅ Checkpoint 3
- [ ] `Setup completed successfully` printed.
- [ ] **Permission Grants: granted** ✅ (or you handed the printed PowerShell to your Global Admin and they ran it).
- [ ] A file `a365.generated.config.json` exists in your project folder.
- [ ] In the Azure portal, the resource group + web app + managed identity all exist.

### 🧠 Practice exercise
Open `a365.generated.config.json` and identify these fields. Write the values into a sticky note — you'll need them later:

| Field | Value |
|---|---|
| `agentBlueprintId` | _____________________ |
| `agentIdentity.appId` | _____________________ |
| `messagingEndpoint` | _____________________ |
| `webAppUrl` | _____________________ |

---

## Lab 4 — Publish + Deploy (~15 min)

Follow [README §5 and §6](README.md#5️⃣-customize-the-teams-manifest-5-minutes).

### Step 4.1
Edit `manifest/manifest.json` — at minimum set `name.short`, `description.short`, `developer.name`, and **two real URLs** for privacy + ToU (your GitHub repo is fine).

### Step 4.2

```powershell
a365 publish
a365 deploy
```

### ✅ Checkpoint 4
- [ ] `Publish completed successfully`.
- [ ] `Deployment completed successfully`.
- [ ] `https://<webAppUrl>/healthz` returns `{"ok": true}` in a browser.

### 🧠 Practice exercise
Open the **Azure portal → your Web App → Log stream**. Hit the `/healthz` endpoint a few times and watch the entries appear. This is the same log stream you'd use to debug a deployed agent.

---

## Lab 5 — Teams blueprint config + first chat (~25 min)

Follow [README §7 and §8](README.md#7️⃣-wire-the-agent-to-teams-5-minutes-one-time).

### ✅ Checkpoint 5
- [ ] In the Teams Developer Portal, your **Notification URL** is saved to your messaging endpoint.
- [ ] You raised an instance request from Teams → **Apps**.
- [ ] An admin **approved** the request at <https://admin.cloud.microsoft/#/agents/all/requested>.
- [ ] In a new Teams chat, your agent name autocompletes.
- [ ] `hello` → `You said: hello` in Teams.

### 🧠 Practice exercise
After your first reply, open the **Web App Log Stream** (Azure portal). You should see the incoming request from Teams. Note the trace ID in the headers — that's what we'll search for in App Insights/Agent 365 next.

> 💤 If `hello` doesn't reply, wait 5 min — agent-user creation is async. If still nothing, see the Troubleshooting Cheat Sheet in the README.

---

## Lab 6 — Observability (~20 min)

Follow [README §9](README.md#9️⃣-add-agent-365-observability-20-minutes) exactly. The three things to add are: (1) imports, (2) one `use_microsoft_opentelemetry(...)` call in `main()`, (3) wrap your message handler body with a baggage scope and register the per-turn token.

```powershell
pip install microsoft-opentelemetry
# add to requirements.txt
a365 deploy
```

### ✅ Checkpoint 6
- [ ] `requirements.txt` includes `microsoft-opentelemetry`.
- [ ] `.env` (and Azure App Settings) has `ENABLE_A365_OBSERVABILITY_EXPORTER=true`.
- [ ] Redeploy succeeded.
- [ ] You sent at least one new message in Teams after the redeploy.

### 🧠 Practice exercise
After your test message, look at the Web App **Log stream** for log lines like `BaggageBuilder` or `register_observability`. If you see exceptions starting with `A365 observability token registration failed:` — read the error. The most common cause: missing the `OtelWrite` app role on the Agent Identity. The README §9.4 troubleshooting box shows the PowerShell to grant it.

---

## Lab 7 — Validate in three portals (~20 min)

### 7.1 Admin Center

Go to <https://admin.cloud.microsoft/#/agents/all>.

### ✅ Check
- [ ] Your agent appears with the name from `manifest.json`.
- [ ] Status is **Active**.

### 7.2 Agent 365 Control Panel

Open your agent's **Telemetry / Observability** tab.

### ✅ Check
- [ ] At least one **turn** shows up (give it 1–5 min after the message).
- [ ] Expanding the turn shows baggage attributes: `tenantId`, `conversationId`, `userId`.

### 7.3 Defender XDR

Run this KQL in **Advanced Hunting**:

```kusto
AgentActivity
| where AgentDisplayName == "<your agent name>"
| top 50 by Timestamp desc
```

### ✅ Check
- [ ] Rows appear (within 5–15 minutes of the first message).

### 🧠 Practice exercise — write your own KQL
Write a query that counts **how many distinct users** have chatted with your agent in the last 24 hours:

<details>
<summary>Answer</summary>

```kusto
AgentActivity
| where Timestamp > ago(24h)
| where AgentDisplayName == "<your agent name>"
| summarize uniqueUsers = dcount(UserPrincipalName)
```

</details>

---

## Lab 8 — Cleanup (~10 min)

When you're done experimenting, **do not leave the resources running** — they cost money.

```powershell
a365 cleanup azure --agent-name <your-initials>-first-agent
a365 cleanup blueprint --agent-name <your-initials>-first-agent
```

### ✅ Checkpoint 8
- [ ] Both cleanup commands report success.
- [ ] In the Azure portal, the resource group is gone.
- [ ] The blueprint is gone from the Teams Developer Portal.

### 🧠 Practice exercise
Re-run `a365 cleanup azure ...` a second time. Notice it succeeds even though there's nothing to delete — the command is **idempotent**. This is why CI/CD jobs that tear down test environments can safely run it.

---

## 🆘 Troubleshooting quick wins

| Symptom | First thing to try |
|---|---|
| `a365: command not found` | New terminal so PATH updates pick up. |
| `Forbidden` during `setup all` | Hand the printed PowerShell script to your Global Admin. |
| Teams autocomplete doesn't show your agent | Wait — agent-user creation can take **hours**. |
| Bot doesn't reply in Teams | Notification URL in Teams Developer Portal wrong/missing. |
| No traces in Control Panel | `ENABLE_A365_OBSERVABILITY_EXPORTER=true` set? Redeployed? `OtelWrite` granted? |
| Defender XDR empty | Wait 5–15 min. Confirm agent name spelling. |
| Browser sign-in loops | Wrong account selected. Sign out, re-run `az login --allow-no-subscriptions`, pick the **work** account. |

See [README troubleshooting cheat sheet](README.md#-troubleshooting-cheat-sheet) for the full table.

---

## 🎓 Self-check

1. **What's the difference between an agent blueprint and an agent instance?**

   <details><summary>Show answer</summary>
   A **blueprint** is the template (registered once in Entra). An **instance** is one approved running copy of that blueprint in your tenant. Many tenants can adopt the same blueprint; each gets its own instance.
   </details>

2. **Where does `a365 setup all` get the secrets it puts in your Web App?**

   <details><summary>Show answer</summary>
   It generates new secrets (or uses managed identity where possible), stores them in the Web App's **App Settings** (or Key Vault), and references them by environment variable name in your code.
   </details>

3. **You see traces in App Insights but not in the Agent 365 Control Panel. Why?**

   <details><summary>Show answer</summary>
   The Microsoft OpenTelemetry exporter has two destinations: Azure Monitor (App Insights) and Agent 365. The Agent 365 destination requires (1) `ENABLE_A365_OBSERVABILITY_EXPORTER=true`, (2) the `OtelWrite` app role on the Agent Identity, and (3) the per-turn token registration via `AgenticTokenCache.register_observability`.
   </details>

4. **What is the smallest thing you must change in `manifest.json` between two different developers running this lab on the same tenant?**

   <details><summary>Show answer</summary>
   The `--agent-name` (which determines the Azure web app name) and `name.short` (so the admin can tell them apart). The `id` and `agenticUserTemplates[].id` are auto-filled by `a365 publish`.
   </details>

5. **Why did the README tell you to do a `--dry-run` first?**

   <details><summary>Show answer</summary>
   To preview what `setup all` would create (resource names, region, permissions) without spending money or polluting your subscription. It's the equivalent of `terraform plan`.
   </details>

---

## 🚀 Bonus tasks

1. **Combine with Phase 6** — add the RAG tool to the wrapped agent so policy questions work in Teams.
2. **Add a Defender detection rule** — see [README §10.4](README.md#104-alerting-bonus). Build the rule that alerts on >100 msgs/10 min.
3. **CI/CD** — wire `a365 deploy` into a GitHub Actions workflow on push to `main`.
4. **Multi-region** — deploy a second instance in a different Azure region and front them with **Front Door**.
5. **Cost guardrails** — set an Azure **Budget Alert** on the resource group at $25/month so you don't get surprised.

---

## 🏁 You're done — with the entire curriculum!

Across 12 phases you have:

- Built echo, routing, stateful, card-driven, LLM-powered, RAG-enabled, Teams + SSO agents.
- Wrapped them with the **Agent 365 enterprise layer**: identity, MCP, notifications, observability.
- Containerized, deployed with `azd`, and monitored in App Insights + Defender XDR.

You're now equipped to design, build, ship, and govern enterprise-grade conversational agents on Microsoft 365 and Azure.

Now go build something amazing — and ping us when it ships. 🎉

🔁 Want to refresh? Jump back to [Phase 0 — Setup](../Phase0_Setup/README.md). Want the big picture? [Curriculum home](../README.md).
