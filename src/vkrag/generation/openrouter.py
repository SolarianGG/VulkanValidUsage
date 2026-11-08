"""OpenRouter client (chat completions) with pinned provider routing and usage accounting.

Routing comes from the config role (`openrouter.answerer_remote` / `openrouter.judge`):
`provider.order`, `allow_fallbacks: false`, `require_parameters: true`, `data_collection: deny`,
optional `quantizations`. Every response is checked against the expected model and provider;
a mismatch is an error (PLAN §5 cache key, §6 risks).
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from dotenv import load_dotenv

from vkrag.config import ROOT, load_config

BASE = "https://openrouter.ai/api/v1"


@dataclass
class Result:
    content: str | None
    reasoning: str | None
    finish_reason: str | None
    model: str | None
    provider: str | None
    usage: dict[str, Any]
    latency_s: float
    gen_id: str | None
    retries: int = 0
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def cost_usd(self) -> float | None:
        return self.usage.get("cost")

    @property
    def reasoning_tokens(self) -> int:
        return (self.usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0

    @property
    def cached_tokens(self) -> int:
        return (self.usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0


def api_key() -> str:
    load_dotenv(ROOT / ".env")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set (.env)")
    return key


class OpenRouter:
    def __init__(self, timeout: float = 180.0, retries: int = 3, backoff_s: float = 5.0):
        self.retries, self.backoff_s = retries, backoff_s
        self.http = httpx.Client(base_url=BASE, timeout=timeout,
                                 headers={"Authorization": f"Bearer {api_key()}", "X-Title": "vkrag"})

    def get(self, path: str, **params) -> dict:
        r = self.http.get(path, params=params or None)
        r.raise_for_status()
        return r.json()

    def key_info(self) -> dict:
        return self.get("/key")["data"]

    def model_info(self, model: str) -> dict | None:
        return next((m for m in self.get("/models")["data"] if m["id"] == model), None)

    def endpoints(self, model: str) -> list[dict]:
        return self.get(f"/models/{model}/endpoints")["data"]["endpoints"]

    def generation(self, gen_id: str, retries: int = 5) -> dict | None:
        """/generation stats (provider, native tokens, cost); available a few seconds after the call."""
        for i in range(retries):
            r = self.http.get("/generation", params={"id": gen_id})
            if r.status_code == 200:
                return r.json()["data"]
            time.sleep(1.5 * (i + 1))
        return None

    def chat(self, role_cfg: dict, messages: list[dict], *, max_tokens: int | None = None,
             response_format: dict | None = None, provider_order: list[str] | None = None,
             extra: dict | None = None) -> Result:
        prov = dict(role_cfg["provider"])
        if provider_order is not None:
            prov["order"] = provider_order
        if not prov.get("order"):
            prov.pop("order", None)
        body: dict[str, Any] = {
            "model": role_cfg["model"],
            "messages": messages,
            "max_tokens": max_tokens or role_cfg["max_tokens"],
            "temperature": role_cfg.get("temperature", 0),
            "provider": prov,
            "usage": {"include": True},
        }
        if role_cfg.get("reasoning") is not None:
            body["reasoning"] = role_cfg["reasoning"]
        if response_format:
            body["response_format"] = response_format
        if extra:
            body.update(extra)
        # PLAN Stage 6 skip policy: up to `retries` retries with backoff on 429 / 5xx / timeouts
        retries_done = 0
        while True:
            t0 = time.perf_counter()
            try:
                r = self.http.post("/chat/completions", json=body)
                transient = r.status_code == 429 or r.status_code >= 500
            except (httpx.TimeoutException, httpx.TransportError):
                r, transient = None, True
            dt = time.perf_counter() - t0
            if not transient or retries_done >= self.retries:
                break
            retries_done += 1
            time.sleep(self.backoff_s * 2 ** (retries_done - 1))
        if r is None:
            raise httpx.TransportError(f"no response after {retries_done} retries")
        if r.status_code != 200:
            raise httpx.HTTPStatusError(f"{r.status_code}: {r.text[:500]}", request=r.request, response=r)
        j = r.json()
        if "error" in j:
            raise RuntimeError(f"OpenRouter error: {j['error']}")
        ch = j["choices"][0]
        msg = ch.get("message") or {}
        return Result(
            content=msg.get("content"),
            reasoning=msg.get("reasoning"),
            finish_reason=ch.get("finish_reason"),
            model=j.get("model"),
            provider=j.get("provider"),
            usage=j.get("usage") or {},
            latency_s=round(dt, 3),
            gen_id=j.get("id"),
            retries=retries_done,
            raw=j,
        )


def role(name: str) -> dict:
    return load_config()["openrouter"][name]
