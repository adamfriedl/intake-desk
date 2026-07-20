"""Embedding helpers — OpenAI by default; swap provider in settings."""

from __future__ import annotations

import httpx

from intake_desk.config import Settings


async def embed_texts(settings: Settings, texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for embeddings")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "authorization": f"Bearer {settings.openai_api_key}",
                "content-type": "application/json",
            },
            json={
                "model": settings.embedding_model,
                "input": texts,
                "dimensions": settings.embedding_dimensions,
            },
        )
        response.raise_for_status()
        data = response.json()

    return [item["embedding"] for item in data["data"]]
