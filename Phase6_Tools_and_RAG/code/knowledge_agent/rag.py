"""Tiny in-memory RAG store.

For learning only. For production use Azure AI Search, Qdrant, Pinecone, etc.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

import numpy as np
from openai import AsyncAzureOpenAI

EMBED_MODEL = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")


def _client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


@dataclass
class Doc:
    title: str
    text: str
    vector: np.ndarray = field(default=None)  # type: ignore[assignment]


class VectorStore:
    def __init__(self) -> None:
        self.docs: List[Doc] = []

    async def add(self, title: str, text: str) -> None:
        emb = await _client().embeddings.create(model=EMBED_MODEL, input=text)
        self.docs.append(Doc(title=title, text=text, vector=np.array(emb.data[0].embedding)))

    async def search(self, query: str, k: int = 3) -> list[Doc]:
        if not self.docs:
            return []
        emb = await _client().embeddings.create(model=EMBED_MODEL, input=query)
        q = np.array(emb.data[0].embedding)
        # cosine similarity
        scores = [
            float(np.dot(q, d.vector) / (np.linalg.norm(q) * np.linalg.norm(d.vector)))
            for d in self.docs
        ]
        order = sorted(range(len(self.docs)), key=lambda i: scores[i], reverse=True)
        return [self.docs[i] for i in order[:k]]


# ---- Seed documents (your "knowledge base") ----
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
    store = VectorStore()
    for title, text in SEED_DOCS:
        await store.add(title, text)
    return store
