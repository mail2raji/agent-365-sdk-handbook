"""LLM helper — wraps Azure OpenAI in two small functions.

KID-FRIENDLY VERSION:
    This file is the WALKIE-TALKIE to the smart cloud robot (the LLM).
    Two ways to talk to it:
      `ask`        → ask a question, wait for the WHOLE answer, return it.
      `ask_stream` → ask, then receive the answer one little piece at a
                     time (like a printer printing word by word).
"""
from __future__ import annotations

import os
# `AsyncAzureOpenAI` = the official OpenAI client, but ASYNC and pointed at Azure.
from openai import AsyncAzureOpenAI

# The SYSTEM message is a hidden instruction the user never sees.
# It tells the LLM "who you are" and "how to behave" for the whole chat.
SYSTEM_PROMPT = (
    "You are 'Buddy', a friendly tutor for kids aged 8-12. "
    "Explain things in simple words. Use short sentences and emojis. "
    "Never make things up — if you don't know, say so."
)
# Only send the LAST N turns to the LLM (cheaper + faster).
MAX_HISTORY = 20


def _client() -> AsyncAzureOpenAI:
    # Build a fresh client each call. Reads keys/endpoint from env vars.
    # `os.environ["X"]` will raise KeyError if X is missing — that's on purpose,
    # so we fail FAST and LOUDLY instead of silently calling with `None`.
    return AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


async def ask(history: list[dict], user_msg: str) -> str:
    """Non-streaming call. Returns the full reply and updates history in place."""
    # 1. Add the new user message to history.
    history.append({"role": "user", "content": user_msg})
    # 2. Build the messages list: SYSTEM prompt first, then the last 20 turns.
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-MAX_HISTORY:]
    # 3. Make the call. `temperature=0.4` = pretty focused (lower = more boring,
    #    higher = more creative). 0.4 is a friendly tutor default.
    resp = await _client().chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=msgs,
        temperature=0.4,
    )
    # 4. Grab the first choice's text (could be None if the LLM returned nothing).
    reply = resp.choices[0].message.content or ""
    # 5. Append the assistant reply to history so the NEXT call sees it.
    history.append({"role": "assistant", "content": reply})
    return reply


async def ask_stream(history: list[dict], user_msg: str):
    """Streaming call. Yields chunks of text as they arrive.

    `yield` makes this an ASYNC GENERATOR — the caller does
    `async for chunk in ask_stream(...)` to get pieces one by one.
    """
    history.append({"role": "user", "content": user_msg})
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-MAX_HISTORY:]
    # `stream=True` tells the client: don't wait for the whole answer —
    # send me each piece ("delta") as soon as the LLM emits it.
    stream = await _client().chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=msgs,
        temperature=0.4,
        stream=True,
    )
    full: list[str] = []                # buffer to rebuild the FULL reply for history
    async for chunk in stream:
        # Each `chunk` is a tiny update. The actual text lives in `.delta.content`.
        if chunk.choices and chunk.choices[0].delta.content:
            piece = chunk.choices[0].delta.content
            full.append(piece)
            yield piece                 # hand this little piece to the caller right now
    # When the stream is finished, save the joined-up reply to history.
    history.append({"role": "assistant", "content": "".join(full)})
