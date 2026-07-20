"""LLM client abstraction — swap Anthropic/OpenAI via settings."""

from __future__ import annotations

import json
from typing import Any

import httpx

from intake_desk.config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def complete(self, system: str, user: str, *, json_mode: bool = False) -> str:
        if self.settings.llm_provider == "anthropic":
            return await self._anthropic(system, user, json_mode=json_mode)
        if self.settings.llm_provider == "openai":
            return await self._openai(system, user, json_mode=json_mode)
        raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")

    async def _anthropic(self, system: str, user: str, *, json_mode: bool) -> str:
        if not self.settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if json_mode:
            payload["messages"][-1]["content"] += "\n\nRespond with valid JSON only."

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def _openai(self, system: str, user: str, *, json_mode: bool) -> str:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "authorization": f"Bearer {self.settings.openai_api_key}",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


def parse_json_response(raw: str) -> dict[str, Any]:
    """Best-effort JSON extraction from model output."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(line for line in lines if not line.startswith("```")).strip()
    return json.loads(text)
