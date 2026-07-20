"""Embedding helpers — OpenRouter by default (OpenAI-compatible); direct OpenAI fallback."""

from __future__ import annotations

import httpx

from intake_desk.config import Settings

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


async def embed_texts(settings: Settings, texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    # Batch in chunks to stay under provider input limits on long corpus ingest.
    batch_size = 64
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        vectors.extend(await _embed_batch(settings, batch))
    return vectors


async def _embed_batch(settings: Settings, texts: list[str]) -> list[list[float]]:
    if settings.openrouter_api_key:
        base_url = OPENROUTER_BASE
        api_key = settings.openrouter_api_key
        headers = {
            "authorization": f"Bearer {api_key}",
            "content-type": "application/json",
            "HTTP-Referer": "https://github.com/adamfriedl/intake-desk",
            "X-OpenRouter-Title": "Intake Desk",
        }
    elif settings.openai_api_key:
        base_url = "https://api.openai.com/v1"
        api_key = settings.openai_api_key
        headers = {
            "authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        }
    else:
        raise RuntimeError("OPENROUTER_API_KEY or OPENAI_API_KEY is required for embeddings")

    payload: dict = {
        "model": settings.embedding_model,
        "input": texts,
    }
    # OpenAI supports dimensions; OpenRouter forwards when the upstream model allows it.
    if settings.embedding_dimensions:
        payload["dimensions"] = settings.embedding_dimensions

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/embeddings",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    # OpenAI/OpenRouter return data sorted by index, but sort defensively.
    items = sorted(data["data"], key=lambda item: item["index"])
    return [item["embedding"] for item in items]
