"""LLM client abstraction — OpenRouter by default; Anthropic/OpenAI still supported."""

from __future__ import annotations

import json
from typing import Any

import httpx

from intake_desk.config import Settings

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def complete(self, system: str, user: str, *, json_mode: bool = False) -> str:
        provider = self.settings.llm_provider
        if provider == "openrouter":
            return await self._openrouter(system, user, json_mode=json_mode)
        if provider == "openai":
            return await self._openai_compatible(
                system,
                user,
                json_mode=json_mode,
                base_url="https://api.openai.com/v1",
                api_key=self.settings.openai_api_key,
                key_name="OPENAI_API_KEY",
            )
        if provider == "anthropic":
            return await self._anthropic(system, user, json_mode=json_mode)
        raise ValueError(f"Unsupported LLM provider: {provider}")

    async def _openrouter(self, system: str, user: str, *, json_mode: bool) -> str:
        return await self._openai_compatible(
            system,
            user,
            json_mode=json_mode,
            base_url=OPENROUTER_BASE,
            api_key=self.settings.openrouter_api_key,
            key_name="OPENROUTER_API_KEY",
            extra_headers={
                "HTTP-Referer": "https://github.com/adamfriedl/intake-desk",
                "X-OpenRouter-Title": "Intake Desk",
            },
        )

    async def _openai_compatible(
        self,
        system: str,
        user: str,
        *,
        json_mode: bool,
        base_url: str,
        api_key: str,
        key_name: str,
        extra_headers: dict[str, str] | None = None,
    ) -> str:
        if not api_key:
            raise RuntimeError(f"{key_name} is not set")

        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "authorization": f"Bearer {api_key}",
            "content-type": "application/json",
            **(extra_headers or {}),
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

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

        async with httpx.AsyncClient(timeout=90.0) as client:
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


def parse_json_response(raw: str) -> dict[str, Any]:
    """Best-effort JSON extraction from model output."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(line for line in lines if not line.startswith("```")).strip()
    return json.loads(text)
