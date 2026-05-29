# 🧩 Phase 0 — Exercises

> Try each exercise first. Only peek at the answer after you've attempted it.
> Many answers are short — that's normal at this stage.

---

## Exercise 1 — Spot the SDK

Which package gives you the `AgentApplication` class?

<details><summary>Answer</summary>

`microsoft-agents-hosting-core`. Imported as:

```python
from microsoft_agents.hosting.core import AgentApplication
```

</details>

---

## Exercise 2 — Two SDKs

Fill in the blanks:

> The **____ ____ ____ SDK** is for *building* the agent.
> The **____ ____ ____ SDK** is for *governing* the agent inside an enterprise.

<details><summary>Answer</summary>

- **Microsoft 365 Agents SDK** — builds the agent.
- **Microsoft Agent 365 SDK** — governance/identity/observability layer.

</details>

---

## Exercise 3 — Underscores vs dots

Python import paths use **underscores** but PyPI package names use **dashes**. Convert:

```
microsoft-agents-hosting-aiohttp   →  from microsoft_agents.hosting.________  import CloudAdapter
microsoft-agents-activity          →  from microsoft_agents.________          import Activity
```

<details><summary>Answer</summary>

```python
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.activity import Activity
```

</details>

---

## Exercise 4 — Activate the venv

Write the command to activate the virtual environment on **Windows PowerShell**, and the equivalent on **macOS/Linux**.

<details><summary>Answer</summary>

```powershell
# Windows
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

</details>

---

## Exercise 5 — Verify Python version

Write one shell command that prints the Python version.

<details><summary>Answer</summary>

```bash
python --version
```

(Or `python3 --version` on macOS/Linux.)

</details>

---

## Exercise 6 — Read the error

You ran your script and saw:

```
ModuleNotFoundError: No module named 'microsoft_agents'
```

What are the two most likely causes?

<details><summary>Answer</summary>

1. Virtual environment is **not active** — activate it (`.\.venv\Scripts\Activate.ps1`).
2. The packages were **not installed** — run `pip install -r requirements.txt`.

</details>

---

## Exercise 7 — Smoke test mistake

You wrote:

```python
from microsoft_agents.hosting.core import AgentApp
```

and got `ImportError`. What's wrong?

<details><summary>Answer</summary>

The class is called **`AgentApplication`**, not `AgentApp`. Class names are case-sensitive and exact.

</details>

---

## Exercise 8 — Channel abstraction

In one sentence, explain *why* the SDK uses a "channel abstraction layer".

<details><summary>Answer</summary>

So you write your agent code **once** and the SDK translates it to whatever format each chat surface (Teams, Slack, web chat, …) expects — instead of you writing a separate integration per channel.

</details>

---

## Exercise 9 — Pick the right Python version

Which Python versions are officially supported by the M365 Agents SDK?

- a) 2.7
- b) 3.6 – 3.8
- c) 3.9 – 3.11
- d) 3.12 only

<details><summary>Answer</summary>

**c) 3.9 – 3.11** is officially supported. Use 3.10 or 3.11 for best results.

</details>

---

## Exercise 10 — Which package?

Match the package name to its job.

| Package | Job |
|---|---|
| A. `microsoft-agents-hosting-aiohttp` | 1. Holds activity data classes |
| B. `microsoft-agents-hosting-core` | 2. Adds Microsoft Teams-specific helpers |
| C. `microsoft-agents-activity` | 3. HTTP server adapter built on `aiohttp` |
| D. `microsoft-agents-hosting-teams` | 4. Core types: `AgentApplication`, `TurnContext`, storage |

<details><summary>Answer</summary>

A → 3, B → 4, C → 1, D → 2.

</details>

---

## Exercise 11 — `.env` files

Why do we store secrets in a `.env` file instead of in `app.py`?

<details><summary>Answer</summary>

So secrets are **not committed to source control**. Add `.env` to `.gitignore`. The code reads them at runtime via `os.environ` (or `python-dotenv`).

</details>

---

## Exercise 12 — Restart and check

You install a new package with `pip install foo`. Do you need to restart VS Code for your script to find it?

<details><summary>Answer</summary>

No — Python re-reads installed packages every time you run a script, **as long as your venv is the active interpreter**. You may need to restart VS Code's *interpreter selection* if it cached the wrong one, but usually just re-running `python myscript.py` is enough.

</details>

---

## Exercise 13 — Bonus: turn vs conversation

Define **turn** and **conversation** in your own words.

<details><summary>Answer</summary>

- **Turn** = one round trip: user message → agent reply.
- **Conversation** = the whole thread, made of many turns, identified by a unique `conversation.id`.

</details>

---

## Exercise 14 — Bonus: what the SDK is NOT

Name three things the M365 Agents SDK is **not**.

<details><summary>Answer</summary>

It is not:
1. An **AI model** (you bring your own — Azure OpenAI, Foundry, etc.).
2. An **orchestration engine** (you can bolt on Semantic Kernel, Agent Framework, LangChain).
3. A **no-code builder** (that's Copilot Studio / Declarative Agents).

</details>

---

✅ When you're done, head to **[Phase 1 — Foundations](../Phase1_Foundations/README.md)**.
