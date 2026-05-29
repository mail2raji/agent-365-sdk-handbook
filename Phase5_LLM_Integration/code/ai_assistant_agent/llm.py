"""LLM helper — wraps Azure OpenAI in two small functions."""
from __future__ import annotations

import os
from openai import AsyncAzureOpenAI

SYSTEM_PROMPT = (
    "You are 'Buddy', a friendly tutor for kids aged 8-12. "
    "Explain things in simple words. Use short sentences and emojis. "
    "Never make things up — if you don't know, say so."
)
MAX_HISTORY = 20


def _client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


async def ask(history: list[dict], user_msg: str) -> str:
    """Non-streaming call. Returns the full reply and updates history in place."""
    history.append({"role": "user", "content": user_msg})
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-MAX_HISTORY:]
    resp = await _client().chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=msgs,
        temperature=0.4,
    )
    reply = resp.choices[0].message.content or ""
    history.append({"role": "assistant", "content": reply})
    return reply


async def ask_stream(history: list[dict], user_msg: str):
    """Streaming call. Yields chunks of text as they arrive."""
    history.append({"role": "user", "content": user_msg})
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-MAX_HISTORY:]
    stream = await _client().chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=msgs,
        temperature=0.4,
        stream=True,
    )
    full: list[str] = []
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            piece = chunk.choices[0].delta.content
            full.append(piece)
            yield piece
    history.append({"role": "assistant", "content": "".join(full)})
