# 🧪 Phase 5 — Hands-On Lab: Build an AI Study Buddy

> A step-by-step lab. By the end you'll have a chat agent powered by **Azure OpenAI** (or regular OpenAI) that remembers your conversation, has a system personality, and streams its replies one word at a time.

---

## 🎯 What you'll build today

A small agent called **`study_buddy`**:

1. Talks to a real LLM (Azure OpenAI's `gpt-4o-mini`, or OpenAI's `gpt-4o-mini`).
2. Has a **system prompt** that gives it a kid-tutor personality.
3. Keeps a **conversation history** so it remembers prior turns.
4. Trims history to the last N messages so it doesn't run out of tokens.
5. Streams the reply token-by-token (an upgrade over waiting for the whole answer).
6. Has a `reset` command to wipe the history.

You'll also learn how to **mock** the LLM so your tests don't burn API credits.

> 👶 Think of the LLM as a very smart parrot. The **system prompt** is the parrot's training. The **history** is what you said in this conversation so far. We hand the parrot both, and it tells us the next word.

⏱️ **About 90 minutes**.

---

## ✅ Before you start

- [ ] Phase 4 finished.
- [ ] Terminal prompt starts with **`(.venv)`**.
- [ ] You have an **Azure OpenAI** resource with a deployed `gpt-4o-mini` model — **OR** a regular OpenAI API key from <https://platform.openai.com/api-keys>.
- [ ] You can edit a `.env` file safely (don't commit it to git).

---

## 🗺️ Today's roadmap

```
Lab 1 → Confirm your API key works (5-line script)
Lab 2 → Build the agent without streaming (the simple flow)
Lab 3 → Add conversation history + system prompt
Lab 4 → Add streaming
Lab 5 → Add a "reset" command
Lab 6 → (Optional) Mock the LLM for tests
```

---

## Lab 1 — Confirm your API key works (~15 min)

**You will:** write a tiny standalone script that asks the LLM one question. If this works, the agent will too.

### Step 1.1 — Make the lab folder

```powershell
cd Phase5_LLM_Integration
mkdir -Force lab_buddy
cd lab_buddy
Copy-Item ..\code\ai_assistant_agent\start_server.py .
```

### Step 1.2 — Create `.env`

```powershell
New-Item .env -ItemType File
code .env
```

For **Azure OpenAI**, paste:

```dotenv
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
AZURE_OPENAI_API_KEY=PUT-YOUR-KEY-HERE
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-10-21
```

For **regular OpenAI**, paste instead:

```dotenv
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

> 🔐 **NEVER** commit `.env` to git. Check that `.gitignore` includes it (it does in this curriculum — but check your forks).

Save.

### Step 1.3 — Make `smoke_test.py`

```powershell
New-Item smoke_test.py -ItemType File
code smoke_test.py
```

Paste (Azure version):

```python
"""smoke_test.py — asks the LLM ONE question to verify your key works."""
import os, asyncio
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

load_dotenv()

async def main():
    client = AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
    resp = await client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": "You are a friendly assistant."},
            {"role": "user", "content": "Say hi in 5 words."},
        ],
    )
    print("Reply:", resp.choices[0].message.content)

asyncio.run(main())
```

For **regular OpenAI**, replace `AsyncAzureOpenAI` and its arguments:

```python
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
# ... and use:
resp = await client.chat.completions.create(
    model=os.environ["OPENAI_MODEL"], messages=[...]
)
```

Save.

### Step 1.4 — Run it

```powershell
python smoke_test.py
```

**Expected output (something like):**

```text
Reply: Hi there! How are you?
```

🎉 Your key works.

#### 🚨 If it fails

| Error | Fix |
|---|---|
| `KeyError: 'AZURE_OPENAI_API_KEY'` | `.env` not loaded — make sure `load_dotenv()` runs and you're in the same folder as `.env`. |
| `401 Unauthorized` | Wrong key. Re-copy from the portal. |
| `404 Not Found … deployment` | The deployment name in `.env` doesn't match the one in Foundry. |
| `ModuleNotFoundError: openai` | Run `pip install openai python-dotenv`. |

### ✅ Checkpoint 1
`smoke_test.py` prints a real reply from the LLM.

---

## Lab 2 — Simple agent (no history, no streaming) (~15 min)

**You will:** wire the same LLM call into an agent.

### Step 2.1 — Create `app_v1.py`

```powershell
New-Item app_v1.py -ItemType File
code app_v1.py
```

Paste:

```python
"""app_v1.py — simplest possible LLM agent. No history, no streaming."""
import os
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from start_server import start_server

load_dotenv()
AGENT_APP = AgentApplication(storage=MemoryStorage())

_client = AsyncAzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
)
DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]


@AGENT_APP.activity("message")
async def chat(context: TurnContext, state: TurnState):
    user_msg = context.activity.text or ""
    resp = await _client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
    )
    reply = resp.choices[0].message.content
    await context.send_activity(reply)


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

Save.

### Step 2.2 — Run & test

```powershell
python app_v1.py
```

```powershell
function Send-Msg {
    param([string]$Text, [string]$User="alice")
    $body = @{ type="message"; text=$Text; from=@{id=$User; name=$User}; recipient=@{id="bot"}; conversation=@{id="c-$User"}; serviceUrl="http://localhost" } | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Uri http://localhost:3978/api/messages -Method POST -ContentType "application/json" -Body $body
}

Send-Msg "What is the capital of France?"
Send-Msg "And what about Germany?"
```

You'll see the response logged in terminal 1 — but notice the **second** question got an answer that didn't know "France" was the previous topic. That's because we sent **no history**. Let's fix that.

### ✅ Checkpoint 2
Agent answers both questions, but the second one shows no memory.

Stop the agent.

---

## Lab 3 — Add history + system prompt (~15 min)

**You will:** make the agent feel like one continuous conversation.

### Step 3.1 — Create `llm.py`

```powershell
New-Item llm.py -ItemType File
code llm.py
```

Paste:

```python
"""llm.py — LLM helper with history trimming and a system prompt."""
import os
from openai import AsyncAzureOpenAI

SYSTEM_PROMPT = (
    "You are 'Buddy', a friendly tutor for kids aged 8–12. "
    "Use short sentences, plain words, and 1–2 emojis per reply. "
    "If you don't know the answer, say so."
)
MAX_HISTORY = 20   # last 20 messages → ~2k tokens, very cheap


def _client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


async def ask(history: list[dict], user_msg: str) -> str:
    history.append({"role": "user", "content": user_msg})
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-MAX_HISTORY:]
    resp = await _client().chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=msgs,
        temperature=0.4,
    )
    reply = resp.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    return reply
```

### Step 3.2 — Create `app_v2.py`

```powershell
New-Item app_v2.py -ItemType File
code app_v2.py
```

Paste:

```python
"""app_v2.py — Buddy with history + system prompt."""
from dotenv import load_dotenv
from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
from start_server import start_server
from llm import ask

load_dotenv()
AGENT_APP = AgentApplication(storage=MemoryStorage())


def get_history(state: TurnState) -> list[dict]:
    return state.conversation.get("history", [])


@AGENT_APP.activity("message")
async def chat(context: TurnContext, state: TurnState):
    history = get_history(state)
    reply = await ask(history, context.activity.text or "")
    # `ask` mutated history in-place — persist it
    state.conversation["history"] = history
    await context.send_activity(reply)


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

### Step 3.3 — Run & test

```powershell
python app_v2.py
```

```powershell
Send-Msg "What is the capital of France?"
Send-Msg "And what about Germany?"
Send-Msg "What was my first question?"      # should mention France
```

🎉 Now the third message proves the agent remembers the conversation.

### ✅ Checkpoint 3
Buddy remembers prior turns. The third question correctly says "you first asked about France."

Stop the agent.

---

## Lab 4 — Add streaming (~15 min)

**You will:** make replies arrive piece by piece (better UX than waiting 5 seconds for a whole answer).

### Step 4.1 — Add `ask_stream` to `llm.py`

Open `llm.py` and append:

```python
async def ask_stream(history: list[dict], user_msg: str):
    """Yields chunks of text as they arrive. Updates history in-place."""
    history.append({"role": "user", "content": user_msg})
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-MAX_HISTORY:]
    stream = await _client().chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=msgs,
        temperature=0.4,
        stream=True,
    )
    pieces: list[str] = []
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            piece = chunk.choices[0].delta.content
            pieces.append(piece)
            yield piece
    history.append({"role": "assistant", "content": "".join(pieces)})
```

Save.

### Step 4.2 — Create `app_v3.py`

```powershell
Copy-Item app_v2.py app_v3.py
code app_v3.py
```

Replace the `chat` handler with:

```python
from llm import ask_stream

@AGENT_APP.activity("message")
async def chat(context: TurnContext, state: TurnState):
    history = get_history(state)
    pieces = []
    print("Buddy: ", end="", flush=True)
    async for piece in ask_stream(history, context.activity.text or ""):
        pieces.append(piece)
        print(piece, end="", flush=True)        # stream to terminal
    print()
    state.conversation["history"] = history
    await context.send_activity("".join(pieces))     # send whole reply once
```

> 🧠 **Why not stream over the channel?** Most channels (including the local emulator) don't support true streaming yet — they expect one whole message per `send_activity`. We **stream into our own terminal** so you can *see* the effect, then send the whole reply at the end.
>
> Teams **does** support a typing indicator while you stream. You'd call `context.streaming_response.queue_text(piece)` and `await context.streaming_response.end_stream()`. We'll keep things simple here.

Save.

### Step 4.3 — Run & test

```powershell
python app_v3.py
Send-Msg "Explain gravity in 3 sentences."
```

In terminal 1 you'll see the reply being printed letter-by-letter — that's the stream.

### ✅ Checkpoint 4
You see the reply arriving piece by piece in terminal 1.

Stop the agent.

---

## Lab 5 — Reset command + welcome (~10 min)

### Step 5.1 — Add `reset` and `welcome` to `app_v3.py`

Insert **before** the catch-all `chat` handler:

```python
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "👋 Hi! I'm Buddy. Ask me a homework question. "
                "Type `reset` to forget our chat."
            )


@AGENT_APP.message("reset")
async def reset(context: TurnContext, state: TurnState):
    state.conversation["history"] = []
    await context.send_activity("🧹 Memory cleared. Ask me something new.")
```

Save & restart.

### Step 5.2 — Verify reset

```powershell
Send-Msg "What is the capital of France?"
Send-Msg "And what about Germany?"
Send-Msg "What was my first question?"     # Buddy says: France
Send-Msg "reset"
Send-Msg "What was my first question?"     # Buddy says: I don't remember anything
```

### ✅ Checkpoint 5
After `reset`, Buddy no longer remembers prior turns.

---

## Lab 6 — (Optional) Mock the LLM (~15 min)

**You will:** write a unit test that doesn't hit the real API. This is essential for CI/CD.

### Step 6.1 — Install pytest

```powershell
pip install pytest pytest-asyncio
```

### Step 6.2 — Create `test_llm.py`

```powershell
New-Item test_llm.py -ItemType File
code test_llm.py
```

Paste:

```python
"""test_llm.py — verifies ask() with a mocked OpenAI client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import llm


@pytest.mark.asyncio
async def test_ask_appends_history_and_returns_reply():
    history = []

    fake_resp = MagicMock()
    fake_resp.choices = [MagicMock(message=MagicMock(content="Gravity pulls things down."))]

    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock(return_value=fake_resp)

    with patch.object(llm, "_client", return_value=fake_client):
        reply = await llm.ask(history, "What is gravity?")

    assert reply == "Gravity pulls things down."
    assert history[-2]["role"] == "user"
    assert history[-2]["content"] == "What is gravity?"
    assert history[-1]["role"] == "assistant"
    assert history[-1]["content"] == "Gravity pulls things down."
```

Save.

### Step 6.3 — Run the test

```powershell
pytest -q
```

You should see:

```text
.                                                                       [100%]
1 passed in 0.XXs
```

🎉 You just tested the LLM logic without spending a cent on tokens.

### ✅ Checkpoint 6
The test passes without any network call.

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| `KeyError: 'AZURE_OPENAI_API_KEY'` | `.env` wasn't loaded. | Make sure `load_dotenv()` runs **before** you access `os.environ`. |
| Replies are weird / too long | The model is wandering. | Tighten the system prompt and lower `temperature` (try `0.2`). |
| Replies take 30+ seconds | The model is slow or your network is. | Stream (Lab 4), or pick a smaller model like `gpt-4o-mini`. |
| `RateLimitError` | Too many requests too fast. | Add `await asyncio.sleep(1)` between requests, or upgrade your quota. |
| The history grows forever | You're not trimming. | The `history[-MAX_HISTORY:]` slice in `ask` keeps it small. |
| Replies come back in **English** even though I asked in German | The system prompt forced English. | Change the system prompt or detect the user's language and pass it in. |
| `openai.AuthenticationError` | Wrong key or expired. | Re-copy from the portal. |

---

## 🎓 Self-check

1. **What are the three roles in the `messages` array?**

   <details><summary>Show answer</summary>

   - `system` — instructions the model always sees first.
   - `user` — what the human typed.
   - `assistant` — what the model said previously.
   </details>

2. **Why do we trim history to the last 20 messages?**

   <details><summary>Show answer</summary>
   Models have a fixed context window (tokens cost money and have a max). Trimming keeps requests cheap and within the limit.
   </details>

3. **Why does the SDK not have a built-in LLM client?**

   <details><summary>Show answer</summary>
   So you can swap OpenAI for Claude, Llama, Gemini, or a local model with no SDK change — the SDK stays AI-agnostic.
   </details>

4. **What's the benefit of streaming?**

   <details><summary>Show answer</summary>
   Users see the first words within ~100ms instead of waiting for the whole reply. Perceived latency is much lower.
   </details>

5. **How do you stop the model from making things up?**

   <details><summary>Show answer</summary>
   Three tricks: (1) clearer system prompt ("If unsure, say so"), (2) lower `temperature`, (3) **ground** it in your data with RAG (Phase 6).
   </details>

---

## 🚀 Bonus tasks

1. **Persona switch** — add `persona pirate` and `persona scientist` commands that change the system prompt for that conversation.
2. **Token counter** — print `prompt_tokens` and `completion_tokens` from `resp.usage` after each turn.
3. **Cost tracker** — multiply tokens by your per-1k rate and accumulate in `state.user["cost_cents"]`.
4. **Function calling preview** — add a `tools` parameter to the create call with a fake `get_time()` schema. Watch the model return `tool_calls`. (This is the doorway to Phase 6.)
5. **OpenAI fallback** — wrap `_client()` in a try/except so it switches to `AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])` if Azure fails.

---

## 🏁 You're done!

You can now:

- Call Azure OpenAI / OpenAI from a handler.
- Build a system prompt + history conversation loop.
- Trim history to keep costs low.
- Stream replies (in terminal; Teams streaming in Phase 7).
- Mock the LLM in tests.

Next → [Phase 6 — Tools & RAG (give the agent two superpowers)](../Phase6_Tools_and_RAG/README.md)
