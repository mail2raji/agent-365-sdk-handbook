# 🧩 Phase 5 — Exercises

## Exercise 1 — Three roles

What are the three `role` values in a chat-completions `messages` array?

<details><summary>Answer</summary>

`system`, `user`, `assistant`. (There's also `tool` — covered in Phase 6.)

</details>

---

## Exercise 2 — System prompt change

Rewrite Buddy's system prompt to make it speak like a pirate.

<details><summary>Answer</summary>

```python
SYSTEM_PROMPT = (
    "Ye be Captain Buddy, a friendly pirate tutor for landlubbers aged 8-12. "
    "Speak in pirate lingo. Keep replies short. Use sea emojis. "
    "Never make up facts — say 'Avast, I dunno!' if unsure."
)
```

</details>

---

## Exercise 3 — Why history?

Why do we send the **whole** history on every request instead of just the new message?

<details><summary>Answer</summary>

The chat completions endpoint is **stateless on the server**. The model has no memory between API calls. We send the full conversation so the model can "remember" prior turns.

</details>

---

## Exercise 4 — History trimming

What does `history[-MAX_HISTORY:]` mean?

<details><summary>Answer</summary>

It takes the **last** `MAX_HISTORY` messages from the list (slice from `-MAX_HISTORY` to the end). Prevents the prompt from growing indefinitely and exceeding token limits.

</details>

---

## Exercise 5 — Lower temperature

What's the effect of `temperature=0` vs `temperature=1.0`?

<details><summary>Answer</summary>

- `0.0` → near-deterministic, focused, repetitive. Best for facts.
- `1.0` → creative, varied, sometimes unexpected. Best for brainstorming.

</details>

---

## Exercise 6 — Catch rate limit

Wrap the `ask` call so the user sees a friendly message on rate-limit errors.

<details><summary>Answer</summary>

```python
import openai

try:
    reply = await ask(history, user_msg)
except openai.RateLimitError:
    await context.send_activity("I'm busy right now. Try again in a few seconds.")
    return
```

</details>

---

## Exercise 7 — Swap to OpenAI (non-Azure)

What two lines do you change to use plain OpenAI instead of Azure OpenAI?

<details><summary>Answer</summary>

In `llm.py`:

```python
from openai import AsyncOpenAI

def _client():
    return AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
```

And use `model=os.environ["OPENAI_MODEL"]` (e.g. `"gpt-4o-mini"`) in the calls — without the Azure deployment indirection.

</details>

---

## Exercise 8 — Per-user system prompt

Let users set their own system prompt with `persona <text>` saved in user-scoped state.

<details><summary>Answer</summary>

```python
import re
PERSONA_RE = re.compile(r"^persona\s+(.+)$", re.IGNORECASE)

@AGENT_APP.message(PERSONA_RE)
async def set_persona(context, state):
    text = PERSONA_RE.match(context.activity.text).group(1).strip()
    state.user["system_prompt"] = text
    await context.send_activity("Persona saved for your profile.")

# In ask() (or a wrapper), check state.user["system_prompt"] first.
```

</details>

---

## Exercise 9 — Max tokens

Hard-cap the reply at 200 tokens.

<details><summary>Answer</summary>

```python
resp = await _client().chat.completions.create(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    messages=msgs,
    temperature=0.4,
    max_tokens=200,
)
```

</details>

---

## Exercise 10 — Counting tokens

Why might we want to count tokens before we call the model?

<details><summary>Answer</summary>

To stay within the context window, control cost, and avoid `BadRequestError: maximum context length`. Use `tiktoken` to count.

</details>

---

## Exercise 11 — Two-step prompt

Implement a "summarize then answer" flow: first ask the model to summarize the user's history, then use that summary as context for the answer.

<details><summary>Answer</summary>

```python
async def summarize(history):
    resp = await _client().chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[{"role": "system", "content": "Summarize this conversation in 3 bullets."},
                  *history],
        temperature=0.0, max_tokens=120,
    )
    return resp.choices[0].message.content

# In chat():
summary = await summarize(history)
history.append({"role": "system", "content": f"Previous chat summary:\n{summary}"})
# then call ask(history, user_msg) but pass a clipped history
```

</details>

---

## Exercise 12 — Streaming basics

In the streaming version, why might you buffer chunks until you hit punctuation?

<details><summary>Answer</summary>

Channels rate-limit how many activities you can send per second. Sending after each token is wasteful and chatty; sending after each clause gives a "typing" feel without spamming the channel.

</details>

---

## Exercise 13 — Stateless mode

When would you **not** keep history?

<details><summary>Answer</summary>

One-shot Q&A (FAQ bot), highly factual tasks where context doesn't help, or pipelines where each turn is independent. Skipping history saves tokens and avoids "context bleed".

</details>

---

## Exercise 14 — Bonus: log token usage

Log how many tokens each call used.

<details><summary>Answer</summary>

```python
resp = await _client().chat.completions.create(...)
log.info(f"tokens: prompt={resp.usage.prompt_tokens}, completion={resp.usage.completion_tokens}")
```

</details>

---

## Exercise 15 — Bonus: function-call placeholder

The chat-completions API supports `tools=[...]` for function calling. Without writing code, what's the difference between providing a tool definition and providing extra `system` text describing the same capability?

<details><summary>Answer</summary>

A tool definition lets the **model decide** to call it and returns a structured JSON request you can execute reliably. A `system` description is just text — the model might *describe* calling the function but cannot make the SDK actually invoke it. Tools = structured, executable. System text = unstructured, advisory.

</details>

---

✅ Next → **[Phase 6 — Tools & RAG](../Phase6_Tools_and_RAG/README.md)**.
