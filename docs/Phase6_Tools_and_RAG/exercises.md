# 🧪 Phase 6 — Hands-On Lab: Build an IT Knowledge Agent with Tools + RAG

> A step-by-step lab. By the end you'll have an agent that **calls Python functions on demand** (function calling) **and answers from your own documents** (Retrieval-Augmented Generation).

---

## 🎯 What you'll build today

A knowledge agent that:

1. Knows when to call `get_weather("Tokyo")` and when to just chat.
2. Knows when to call `reset_password("alice@contoso.com")`.
3. Knows when to **search your policy docs** with `lookup_policy("password rotation")`.
4. Combines all three in the same conversation — the model decides which tool to use.

You'll also learn:

- The **two-trip pattern**: model → tool → model → user.
- The **RAG recipe**: chunk → embed → retrieve → augment → answer.
- A 50-line in-memory vector store (no Azure AI Search needed).

> 👶 Think of the agent like a kid with two superpowers:
> - **Tools** — it can press buttons to do things (call your Python functions).
> - **RAG** — it can flip through your book of rules before answering ("hmm, the policy says…").

⏱️ **About 120 minutes**.

---

## ✅ Before you start

- [ ] Phase 5 finished — `smoke_test.py` worked, you have `.env` with API keys.
- [ ] Terminal prompt starts with **`(.venv)`**.
- [ ] `numpy` installed (`pip install numpy` — it's in requirements.txt anyway).
- [ ] Your `.env` also has an **embedding** deployment if using Azure. Add:

  ```dotenv
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
  ```

  In Foundry: Deployments → Deploy model → choose `text-embedding-3-small` → name it the same.

---

## 🗺️ Today's roadmap

```
Lab 1 → Build the tool loop with ONE tool (get_weather)
Lab 2 → Add a second tool (reset_password)
Lab 3 → Build a tiny RAG store (50 lines)
Lab 4 → Wire RAG as a third tool (lookup_policy)
Lab 5 → Live test all three superpowers in one conversation
```

---

## Lab 1 — Tool loop with one tool (~25 min)

**You will:** make the LLM call `get_weather` on its own.

### Step 1.1 — Setup

```powershell
cd Phase6_Tools_and_RAG
mkdir -Force lab_knowledge
cd lab_knowledge
Copy-Item ..\code\knowledge_agent\start_server.py .
# Copy the .env from Phase 5
Copy-Item ..\..\Phase5_LLM_Integration\lab_buddy\.env .
```

### Step 1.2 — Make `tools_v1.py`

```powershell
New-Item tools_v1.py -ItemType File
code tools_v1.py
```

Paste:

```python
"""tools_v1.py — one tool: get_weather."""

# The Python implementation
def get_weather(city: str) -> str:
    # 🌦️ In real life you'd call a weather API. We mock it.
    fake = {"tokyo": "22°C, sunny", "berlin": "12°C, cloudy", "lagos": "31°C, humid"}
    return fake.get(city.lower(), "I don't have weather data for that city.")


# The JSON schema the LLM sees
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name."},
                },
                "required": ["city"],
            },
        },
    },
]

# Map name → function so we can dispatch by string
DISPATCH = {"get_weather": get_weather}
```

> 🧠 **The schema is the LLM's view.** The model sees only the name, description, and parameters — never the Python code. The LLM decides whether to call the tool and what arguments to pass.

### Step 1.3 — Make `app_v1.py`

```powershell
New-Item app_v1.py -ItemType File
code app_v1.py
```

Paste:

```python
"""app_v1.py — agent with the tool loop pattern (one tool)."""
import os, json
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from start_server import start_server
from tools_v1 import TOOL_SCHEMAS, DISPATCH

load_dotenv()
AGENT_APP = AgentApplication(storage=MemoryStorage())

_client = AsyncAzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
)
DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]

SYSTEM = "You are an IT assistant. Use tools when relevant."


async def run_with_tools(history: list[dict], user_msg: str) -> str:
    history.append({"role": "user", "content": user_msg})

    # 🔁 The loop. Up to 5 iterations to prevent infinite tool calls.
    for _ in range(5):
        resp = await _client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[{"role": "system", "content": SYSTEM}] + history,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        msg = resp.choices[0].message
        history.append(msg.model_dump())   # add the assistant turn (with tool_calls if any)

        if not msg.tool_calls:
            return msg.content              # final answer — done

        # The model wants to call ≥1 tools
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)
            print(f"[TOOL CALL] {name}({args})")
            result = DISPATCH[name](https://github.com/mail2raji/agent-365-sdk-handbook/blob/main/Phase6_Tools_and_RAG/**args)
            history.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })
    return "(too many tool calls, stopping)"


@AGENT_APP.activity("message")
async def chat(context: TurnContext, state: TurnState):
    history = state.conversation.get("history", [])
    reply = await run_with_tools(history, context.activity.text or "")
    state.conversation["history"] = history
    await context.send_activity(reply)


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

Save.

### Step 1.4 — Run & test

```powershell
python app_v1.py
```

```powershell
function Send-Msg {
    param([string]$Text, [string]$User="alice")
    $body = @{ type="message"; text=$Text; from=@{id=$User; name=$User}; recipient=@{id="bot"}; conversation=@{id="c-$User"}; serviceUrl="http://localhost" } | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Uri http://localhost:3978/api/messages -Method POST -ContentType "application/json" -Body $body
}

Send-Msg "Tell me a joke."                    # → no tool used (plain reply)
Send-Msg "What's the weather in Tokyo?"        # → tool: get_weather("Tokyo")
Send-Msg "And what about Berlin?"              # → tool: get_weather("Berlin")
```

Terminal 1 should print:

```text
[TOOL CALL] get_weather({'city': 'Tokyo'})
[TOOL CALL] get_weather({'city': 'Berlin'})
```

The first message (joke) doesn't call any tool — the model just chats.

### ✅ Checkpoint 1
The model autonomously decides when to call `get_weather` and the result appears in the reply.

Stop the agent.

---

## Lab 2 — Add the second tool (`reset_password`) (~10 min)

### Step 2.1 — Extend `tools_v1.py` into `tools_v2.py`

```powershell
Copy-Item tools_v1.py tools_v2.py
code tools_v2.py
```

Add another function and another schema:

```python
def reset_password(user_email: str) -> str:
    return f"Done. A temporary password was emailed to {user_email}."

# Append to the existing TOOL_SCHEMAS list
TOOL_SCHEMAS.append({
    "type": "function",
    "function": {
        "name": "reset_password",
        "description": "Reset the user's password. Use ONLY when the user explicitly asks to reset.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_email": {"type": "string", "description": "User email address."},
            },
            "required": ["user_email"],
        },
    },
})

DISPATCH["reset_password"] = reset_password
```

### Step 2.2 — Point `app_v1.py` at `tools_v2`

In `app_v1.py`, change the import:

```python
from tools_v2 import TOOL_SCHEMAS, DISPATCH
```

Save & restart.

### Step 2.3 — Test

```powershell
Send-Msg "Please reset my password — jane@contoso.com"
```

Terminal 1:

```text
[TOOL CALL] reset_password({'user_email': 'jane@contoso.com'})
```

The reply confirms the temp password was emailed.

### ✅ Checkpoint 2
Two tools available. The LLM picks the right one per message.

Stop the agent.

---

## Lab 3 — Build a 50-line RAG store (~20 min)

**You will:** make a tiny vector store that can find relevant docs by meaning.

### Step 3.1 — Create policy docs

```powershell
mkdir -Force docs
@"
# Password Policy
- Passwords must be at least 12 characters.
- Rotate every 90 days.
- Cannot reuse the last 12 passwords.
- Use MFA for all production systems.
"@ | Out-File docs\password.md -Encoding utf8

@"
# VPN Policy
- Connect via Contoso VPN before accessing internal systems.
- Split-tunneling is disabled.
- VPN sessions expire after 24h of inactivity.
"@ | Out-File docs\vpn.md -Encoding utf8

@"
# Travel Policy
- Book flights via Concur at least 14 days in advance.
- Economy class for flights under 6 hours.
- Per diem: $75 per day in EU, $100 in US.
"@ | Out-File docs\travel.md -Encoding utf8
```

### Step 3.2 — Create `rag.py`

```powershell
New-Item rag.py -ItemType File
code rag.py
```

Paste:

```python
"""rag.py — tiny in-memory vector store using NumPy."""
import os, pathlib
import numpy as np
from openai import AsyncAzureOpenAI


_chunks: list[str] = []
_vectors: np.ndarray | None = None


def _client():
    return AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


def _split(text: str, max_chars: int = 500) -> list[str]:
    """Naive splitter: by paragraph, capped at max_chars."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    out = []
    for p in paras:
        if len(p) <= max_chars:
            out.append(p)
        else:
            for i in range(0, len(p), max_chars):
                out.append(p[i:i + max_chars])
    return out


async def _embed(texts: list[str]) -> np.ndarray:
    resp = await _client().embeddings.create(
        model=os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
        input=texts,
    )
    return np.array([d.embedding for d in resp.data])


async def index_folder(folder: str) -> None:
    global _chunks, _vectors
    _chunks = []
    files = pathlib.Path(folder).rglob("*.md")
    for f in files:
        for chunk in _split(f.read_text(encoding="utf-8")):
            _chunks.append(f"# Source: {f.name}\n{chunk}")
    _vectors = await _embed(_chunks)
    print(f"[RAG] indexed {len(_chunks)} chunks from {folder}")


async def search(question: str, top_k: int = 3) -> list[str]:
    if _vectors is None or not len(_chunks):
        return []
    qvec = (await _embed([question]))[0]
    # cosine similarity
    sims = _vectors @ qvec / (np.linalg.norm(_vectors, axis=1) * np.linalg.norm(qvec) + 1e-9)
    top_idx = sims.argsort()[::-1][:top_k]
    return [_chunks[i] for i in top_idx]
```

### Step 3.3 — Smoke test it

Create `rag_smoke.py`:

```python
"""rag_smoke.py — index the docs and ask one question."""
import asyncio
from dotenv import load_dotenv
from rag import index_folder, search

load_dotenv()

async def main():
    await index_folder("./docs")
    hits = await search("How often do I rotate my password?")
    for i, h in enumerate(hits, 1):
        print(f"--- HIT {i} ---")
        print(h)
        print()

asyncio.run(main())
```

Run:

```powershell
python rag_smoke.py
```

You should see:

```text
[RAG] indexed 3 chunks from ./docs
--- HIT 1 ---
# Source: password.md
# Password Policy
- Passwords must be at least 12 characters.
...
```

The password doc is the top hit. 🎉

### ✅ Checkpoint 3
RAG retrieves the most relevant chunk for the question.

---

## Lab 4 — Wire RAG as a third tool (~15 min)

### Step 4.1 — Extend tools

Create `tools_v3.py`:

```powershell
Copy-Item tools_v2.py tools_v3.py
code tools_v3.py
```

Add to `tools_v3.py`:

```python
import asyncio
from rag import search as rag_search


def lookup_policy(question: str) -> str:
    """Returns the top 3 policy chunks as a single string."""
    hits = asyncio.get_event_loop().run_until_complete(rag_search(question))
    if not hits:
        return "No relevant policy found."
    return "\n\n---\n\n".join(hits)


TOOL_SCHEMAS.append({
    "type": "function",
    "function": {
        "name": "lookup_policy",
        "description": "Look up Contoso IT policy on a given topic. Use for any 'what is our policy on X' question.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The user's policy question."},
            },
            "required": ["question"],
        },
    },
})

DISPATCH["lookup_policy"] = lookup_policy
```

> ⚠️ The `asyncio.get_event_loop().run_until_complete(...)` is a quick hack so a sync function can call an async one. In a real app, refactor `run_with_tools` to support async tools natively (bonus task at the end).

### Step 4.2 — Boot RAG at startup

Edit `app_v1.py`:

1. Change the import:

   ```python
   from tools_v3 import TOOL_SCHEMAS, DISPATCH
   from rag import index_folder
   ```

2. At the **bottom**, replace the `if __name__ ==` block:

   ```python
   if __name__ == "__main__":
       import asyncio
       asyncio.run(index_folder("./docs"))
       start_server(AGENT_APP, None)
   ```

Save.

### Step 4.3 — Run

```powershell
python app_v1.py
```

You should see `[RAG] indexed 3 chunks from ./docs` before the server starts.

---

## Lab 5 — End-to-end test (~10 min)

```powershell
Send-Msg "What is our password rotation policy?"           # → lookup_policy
Send-Msg "Reset my password for alice@contoso.com"          # → reset_password
Send-Msg "What's the weather in Lagos?"                     # → get_weather
Send-Msg "Tell me a fun fact about octopuses."              # → no tool
```

Terminal 1 should show:

```text
[TOOL CALL] lookup_policy({'question': 'password rotation policy'})
[TOOL CALL] reset_password({'user_email': 'alice@contoso.com'})
[TOOL CALL] get_weather({'city': 'Lagos'})
```

And no `[TOOL CALL]` for the octopus question.

### ✅ Checkpoint 5
All three tools fire when appropriate, and the LLM chats freely when no tool is needed.

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| The model uses a tool for everything (even chit-chat) | Tool descriptions too greedy. | Tighten the description: "Use ONLY when the user explicitly asks…" |
| Tool never fires | Description too vague, or `tool_choice="none"`. | Make the description specific; ensure `tool_choice="auto"`. |
| `ValueError: 'tool' role must follow a tool_call message` | You appended a tool message without the prior assistant message containing the matching `tool_call_id`. | Make sure you append the assistant turn (with its `tool_calls`) **before** appending the `tool` result. |
| `RuntimeError: event loop already running` | The `asyncio.get_event_loop().run_until_complete(...)` hack is being called inside an already-running loop. | Refactor to native async (bonus task #1). |
| `KeyError: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'` | You didn't add it to `.env`. | Add the env var and the deployment in Foundry. |
| `lookup_policy` returns "No relevant policy found." | `index_folder` failed silently. | Make sure `await index_folder("./docs")` ran at startup and printed the chunk count. |

---

## 🎓 Self-check

1. **What are the two "trips" to the model in the tool loop?**

   <details><summary>Show answer</summary>
   Trip 1: send the conversation + tool schemas; the model returns `tool_calls`. Trip 2: send the tool results back; the model returns a final reply.
   </details>

2. **What does the LLM see — your Python code or the JSON schema?**

   <details><summary>Show answer</summary>
   Only the JSON schema (name, description, parameters). It never sees the implementation. That's why descriptions are critical — they're the model's only clue when to use the tool.
   </details>

3. **What are the 4 steps of RAG?**

   <details><summary>Show answer</summary>
   1. **Chunk** docs into ~500-char pieces. 2. **Embed** each chunk into a vector. 3. **Retrieve** top-k matches for the user's question (cosine similarity). 4. **Augment** the prompt with those chunks and let the LLM answer.
   </details>

4. **Why is RAG better than putting all your docs in the system prompt?**

   <details><summary>Show answer</summary>
   Docs can be huge — too big for the context window and very expensive. RAG sends only the few chunks that matter for *this* question.
   </details>

5. **When would you swap the in-memory store for Azure AI Search?**

   <details><summary>Show answer</summary>
   When docs change between restarts, when you need hybrid (keyword + vector) search, when the corpus exceeds RAM, or when you need to share the index across multiple agents.
   </details>

---

## 🚀 Bonus tasks

1. **Native async tools** — refactor `run_with_tools` to await async functions, and rewrite `lookup_policy` as `async def`.
2. **Citations** — modify `lookup_policy` to return chunks with their source file, then update the system prompt: "Quote sources in your reply, like (source: password.md)."
3. **Hybrid retrieval** — add a keyword filter (`if "password" in chunk.lower(): boost`) on top of cosine.
4. **Persistent vector store** — pickle `_vectors` to disk so you don't re-embed on every restart.
5. **Azure AI Search** — install `azure-search-documents`, create an index, swap `rag.search` for an `AISearchClient.search(...)` call.

---

## 🏁 You're done!

You can now:

- Define a Python function + JSON schema and wire it as an LLM tool.
- Implement the tool loop (model → tool → model → user).
- Chunk docs, embed them, search by cosine, and answer with RAG.
- Combine multiple tools (mock actions + RAG) in one conversation.

Next → [Phase 7 — Multi-channel, Teams & Auth](../Phase7_Channels_Teams_Auth/README.md)
