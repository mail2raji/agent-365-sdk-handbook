# 🧩 Phase 6 — Exercises

## Exercise 1 — Two trips

Why do tool-enabled chats require **two** LLM calls minimum?

<details><summary>Answer</summary>

Call 1: model decides *which* tool to call with what arguments. You then run the function locally. Call 2: model receives the tool result and crafts the user-facing reply.

</details>

---

## Exercise 2 — Add a tool

Add a `get_time(timezone)` tool that returns the current time in the requested timezone.

<details><summary>Answer</summary>

```python
from datetime import datetime
from zoneinfo import ZoneInfo

def get_time(timezone: str) -> str:
    return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M %Z")

# add to DISPATCH/call_tool
# and to TOOLS:
{
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "Get current local time in an IANA timezone like 'Europe/Berlin'.",
        "parameters": {
            "type": "object",
            "properties": {"timezone": {"type": "string"}},
            "required": ["timezone"],
        },
    },
}
```

</details>

---

## Exercise 3 — Tool choice

What does `tool_choice="auto"` vs `tool_choice="required"` mean?

<details><summary>Answer</summary>

- `"auto"` — model decides whether to call a tool.
- `"required"` — model **must** call one of the tools.
- `{"type":"function","function":{"name":"X"}}` — force a specific tool.
- `"none"` — never call a tool.

</details>

---

## Exercise 4 — Schema enum

Make `get_weather` accept only specific cities via an `enum`.

<details><summary>Answer</summary>

```python
"parameters": {
    "type": "object",
    "properties": {
        "city": {"type": "string", "enum": ["Berlin", "Tokyo", "London"]}
    },
    "required": ["city"],
}
```

</details>

---

## Exercise 5 — Loop cap

Why cap the tool loop at, say, 5 iterations?

<details><summary>Answer</summary>

To avoid runaway loops that burn tokens forever if the model keeps requesting tools but never produces a final answer (e.g. due to a buggy tool that returns errors).

</details>

---

## Exercise 6 — Cosine similarity

What does cosine similarity measure?

<details><summary>Answer</summary>

The angle between two vectors. 1 = identical direction (same meaning), 0 = orthogonal (unrelated), -1 = opposite. Independent of vector magnitude, which is why it works well for embeddings.

</details>

---

## Exercise 7 — Chunk size

A doc is 4,000 tokens. You chunk into 500-token pieces with 50-token overlap. How many chunks?

<details><summary>Answer</summary>

Effective stride is 450 tokens, so `ceil((4000 - 500) / 450) + 1` ≈ 9 chunks. Overlap prevents a sentence from being awkwardly split.

</details>

---

## Exercise 8 — Add a doc

Add a new policy to the seed list: "Lunch is from 12:00–13:00."

<details><summary>Answer</summary>

In `rag.py` append to `SEED_DOCS`:

```python
("Lunch Policy", "Lunch break is from 12:00 to 13:00 local time."),
```

Then ask the agent "What time is lunch?" — it should call `lookup_policy` and quote the new doc.

</details>

---

## Exercise 9 — Hallucination guard

The model invented a "VIP weekend bonus" policy. How do you fix the prompt?

<details><summary>Answer</summary>

Strengthen the system prompt:

```text
You MUST only answer from `lookup_policy` results. If the documents don't cover it, say "I couldn't find that in our docs."
```

</details>

---

## Exercise 10 — Why not pass all docs?

Why not just dump every policy doc into the system prompt instead of doing RAG?

<details><summary>Answer</summary>

- Token cost: every call would re-send all docs.
- Context window limits.
- Lower signal-to-noise = worse answers.
- RAG sends only the **relevant** 2-3 chunks per question.

</details>

---

## Exercise 11 — Replace the store

Sketch how you'd swap `VectorStore` for Azure AI Search.

<details><summary>Answer</summary>

1. Create an index with a vector field (`contentVector` of dim 1536).
2. On startup or via a separate indexer, upload embedded chunks.
3. In `search()`, call `SearchClient.search(vector_queries=[VectorizedQuery(...)])`.
4. Map results back to your `Doc` shape.

The agent code never changes — only `rag.py`.

</details>

---

## Exercise 12 — Mixed semantic + keyword

Why might you use *hybrid* search (semantic + keyword) instead of pure vector?

<details><summary>Answer</summary>

Vector search misses exact strings (e.g. error codes, IDs, product names). Hybrid search uses both BM25 keyword + vector similarity, then re-ranks. Better recall on technical content.

</details>

---

## Exercise 13 — Multi-tool call

In one user message, the model decides to call BOTH `get_weather('Berlin')` AND `get_time('Europe/Berlin')`. How does our loop handle it?

<details><summary>Answer</summary>

`msg.tool_calls` is a **list**. We iterate every call, append every `tool` result with the matching `tool_call_id`, then loop. The next LLM call sees all results and answers.

</details>

---

## Exercise 14 — Argument validation

What happens if the model passes `{"city": 123}` (a number, not a string)?

<details><summary>Answer</summary>

`json.loads` succeeds. `get_weather(city=123)` runs and returns nonsense. Defensive fix: validate types in your wrapper with `pydantic` models, raise a clear error, return it as the tool's content string. The model often self-corrects on the next turn.

</details>

---

## Exercise 15 — Bonus: citations

Make `lookup_policy` return numbered citations (`[1] Title: text`) and instruct the model to mention them in the reply.

<details><summary>Answer</summary>

```python
async def lookup_policy(question: str) -> str:
    hits = await STORE.search(question, k=3)
    return "\n".join(f"[{i+1}] {d.title}: {d.text}" for i, d in enumerate(hits))
```

System prompt:

```text
When you use lookup_policy, cite using [1], [2], etc.
```

</details>

---

✅ Next → **[Phase 7 — Multi-channel, Teams & Auth](../Phase7_Channels_Teams_Auth/README.md)**.
