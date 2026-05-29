# 🧩 Phase 10 — Capstone exercises

These are **graded** by the acceptance checklist in [README.md](README.md). For each
exercise, the *answer* is "show working code in the capstone".

## Exercise 1 — Run the scaffold

Get `python app.py` to start and reply "(scaffold) I heard '...'" in the Emulator.

<details><summary>Answer</summary>

Copy `.env.example` to `.env`, activate your venv, run `python app.py`, open Emulator at `http://localhost:3978/api/messages` and type any text.

</details>

---

## Exercise 2 — Wire the LLM fallback

Replace the `(scaffold)` fallback in `app.py` with a real Azure OpenAI call (use Phase 5 `llm.py`).

<details><summary>Answer</summary>

Adapt `llm.py` from Phase 5 and replace `fallback`:

```python
from llm import ask
@AGENT_APP.activity("message")
async def fallback(context, state):
    history = state.conversation.get("history", [])
    reply = await ask(history, context.activity.text or "")
    state.conversation["history"] = history
    await context.send_activity(reply)
```

</details>

---

## Exercise 3 — Add the policy lookup

Implement `lookup_policy` so it loads everything in `docs/` and uses Phase 6 RAG.

<details><summary>Answer</summary>

Add a build step on startup:

```python
async def build_store():
    store = VectorStore()
    for p in pathlib.Path("docs").glob("*.md"):
        await store.add(p.stem, p.read_text())
    return store
```

In `tools.lookup_policy`, search the store and return top 3 chunks.

</details>

---

## Exercise 4 — Wire the ticket form

Show the form on `request ticket`, intercept submissions on `activity("message")`, and reply with the confirmation card.

<details><summary>Answer</summary>

```python
from microsoft_agents.activity import Activity, Attachment
from cards.ticket_form import build_ticket_form
from cards.ticket_confirm import build_ticket_confirmation
from tools import create_ticket

@AGENT_APP.message("request ticket")
async def show(context, state):
    att = Attachment(content_type="application/vnd.microsoft.card.adaptive", content=build_ticket_form())
    await context.send_activity(Activity(type="message", attachments=[att]))

@AGENT_APP.activity("message")
async def maybe(context, state):
    data = context.activity.value
    if data and data.get("action") == "submit_ticket":
        ticket_id = create_ticket(data["title"], data["severity"], data.get("body", ""))
        att = Attachment(content_type="application/vnd.microsoft.card.adaptive",
                         content=build_ticket_confirmation(ticket_id, data))
        await context.send_activity(Activity(type="message", attachments=[att]))
```

</details>

---

## Exercise 5 — Add SSO

Hook MSAL from Phase 7 so `who am i` works.

<details><summary>Answer</summary>

Initialize `AUTH = MsalAuth(connection_name=os.environ["OAUTH_CONNECTION_NAME"])`, pass to `AgentApplication(auth=AUTH)`, add `login`/`logout`/`who am i` handlers calling Graph `/me` with the token.

</details>

---

## Exercise 6 — Persist tickets

Replace the in-memory `TICKETS` list with state stored under `state.user["tickets"]`.

<details><summary>Answer</summary>

In `create_ticket`, accept the state object and `state.user.setdefault("tickets", []).append({...})`. Add a `my tickets` command that lists them per user.

</details>

---

## Exercise 7 — Add OTel

Add one call to `configure_otel(...)` and verify a trace appears in App Insights after one turn.

<details><summary>Answer</summary>

```python
from microsoft_agents_a365.observability.otlp import configure_otel
configure_otel(service_name="contoso-it-companion",
               endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"])
```

In App Insights → **Transaction search** filter by the service name.

</details>

---

## Exercise 8 — Write a test

Write a pytest that verifies the LLM fallback is called when no command matches.

<details><summary>Answer</summary>

Mock the LLM in `llm.ask` and assert the TestAdapter receives the mocked reply for an unknown input like "asdf".

</details>

---

## Exercise 9 — Containerize

Build the Docker image and run it locally with `--env-file .env`.

<details><summary>Answer</summary>

Place `deploy/Dockerfile` (from Phase 9) in the project root; build:

```powershell
docker build -t contoso-it-companion:dev -f deploy/Dockerfile .
docker run --rm -p 3978:3978 --env-file .env contoso-it-companion:dev
```

</details>

---

## Exercise 10 — Deploy

`azd up` and update your Bot Messaging endpoint to the resulting URL.

<details><summary>Answer</summary>

Place `deploy/main.bicep` and `deploy/azure.yaml` from Phase 9 (adjust container image param). Run:

```powershell
azd auth login
azd up
```

Copy the printed `appUrl`, add `/api/messages`, paste it into the Azure Bot resource **Messaging endpoint**.

</details>

---

## Exercise 11 — Side-load in Teams

Zip the manifest folder and upload to Teams.

<details><summary>Answer</summary>

```powershell
Compress-Archive teams_manifest\* -DestinationPath app.zip
```

In Teams → **Apps → Manage your apps → Upload a custom app → Upload for me or my teams** → select `app.zip`.

</details>

---

## Exercise 12 — Demo run

Run the demo script in [README.md](README.md). Capture screenshots.

<details><summary>Answer</summary>

Done when each numbered step in the demo script reproduces the expected reply.

</details>

---

## Exercise 13 — Reflect

Write 5 bullets in `REFLECTION.md`: what surprised you, what was hardest, what's still unclear, what you'd build next, what you'd change about the curriculum.

<details><summary>Answer</summary>

There's no wrong answer — the act of writing it cements the learning. Tip: re-read it next month.

</details>

---

🎓 You're done. Add the capstone to your portfolio.
