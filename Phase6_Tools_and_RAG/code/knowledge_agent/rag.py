"""Tiny in-memory RAG store.

For learning only. For production use Azure AI Search, Qdrant, Pinecone, etc.

KID-FRIENDLY VERSION:
    Pretend you have a SHELF of index cards. Each card has a title +
    a paragraph. We turn each card into a list of numbers (a "vector")
    using the embedding model — think of it as a coordinate on a giant map.
    When the user asks a question, we turn the QUESTION into a vector too,
    then find the 3 cards whose coordinates are closest. Those are the
    cards most likely to answer the question.
"""
from __future__ import annotations

import os
# `dataclass` = Python's way to make a tidy data-holding class with one line.
# `field(default=...)` lets us give a default value to a mutable field.
from dataclasses import dataclass, field
from typing import List

# `numpy` = fast math on arrays. We use it for dot products + norms.
import numpy as np
from openai import AsyncAzureOpenAI

# The embedding model turns text into a vector of ~1500 numbers.
# `text-embedding-3-small` is the cheap, fast default.
EMBED_MODEL = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")


def _client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


@dataclass
class Doc:
    # One index card: title + paragraph + the coordinate-on-the-map vector.
    title: str
    text: str
    vector: np.ndarray = field(default=None)  # type: ignore[assignment]


class VectorStore:
    def __init__(self) -> None:
        # The shelf — starts empty.
        self.docs: List[Doc] = []

    async def add(self, title: str, text: str) -> None:
        # Ask the embedding model to turn `text` into a vector.
        emb = await _client().embeddings.create(model=EMBED_MODEL, input=text)
        # Wrap it in numpy so we can do fast math later.
        self.docs.append(Doc(title=title, text=text, vector=np.array(emb.data[0].embedding)))

    async def search(self, query: str, k: int = 3) -> list[Doc]:
        if not self.docs:
            return []
        # 1. Turn the user's question into a vector too.
        emb = await _client().embeddings.create(model=EMBED_MODEL, input=query)
        q = np.array(emb.data[0].embedding)
        # 2. COSINE SIMILARITY — measures the ANGLE between two vectors.
        #    1.0 = same direction (perfect match), 0 = unrelated, -1 = opposite.
        #    Formula: dot(q, d) / (|q| * |d|).
        scores = [
            float(np.dot(q, d.vector) / (np.linalg.norm(q) * np.linalg.norm(d.vector)))
            for d in self.docs
        ]
        # 3. Sort by score, take the top k.
        order = sorted(range(len(self.docs)), key=lambda i: scores[i], reverse=True)
        return [self.docs[i] for i in order[:k]]


# ---- Seed documents (your "knowledge base") ----
# In a real agent these would come from SharePoint, Confluence, etc.
# Here we hardcode 5 so the demo works offline.
SEED_DOCS = [
    (
        "Password Policy",
        "Passwords must be at least 14 characters, include one number and one symbol, "
        "and be rotated every 90 days. To reset, run /reset or contact the helpdesk.",
    ),
    (
        "VPN Access",
        "All remote users must connect via Contoso VPN before accessing internal apps. "
        "Install the Contoso VPN client from the Software Center.",
    ),
    (
        "MFA Setup",
        "Multi-factor authentication is required. Use the Microsoft Authenticator app. "
        "If you lose your phone, contact the IT helpdesk to reset MFA.",
    ),
    (
        "Laptop Replacement",
        "Standard laptop refresh is every 4 years. To request an early replacement, "
        "open a ticket with your manager's approval.",
    ),
    (
        "Travel Booking",
        "Use Concur to book all travel. Flights must be economy unless duration exceeds 6 hours.",
    ),
]


async def build_default_store() -> VectorStore:
    # Build a fresh store and load all 5 seed docs into it.
    store = VectorStore()
    for title, text in SEED_DOCS:
        await store.add(title, text)
    return store
