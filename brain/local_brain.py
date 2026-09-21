"""Local LLM adapter.

Uses an OpenAI-compatible local llama-server endpoint. No cloud API is required.
Set LOCAL_LLM_URL in the environment if your local server uses another address.
"""
from __future__ import annotations

import os
from typing import Any

import requests


class LocalBrainError(RuntimeError):
    pass


class LocalBrain:
    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: int = 120):
        self.base_url = (base_url or os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1")).rstrip("/")
        self.model = model or os.getenv("LOCAL_LLM_MODEL", "local-model")
        self.timeout = timeout

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 1024) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, KeyError, IndexError, TypeError) as exc:
            raise LocalBrainError(f"Local model request failed: {exc}") from exc

    def ask(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)
