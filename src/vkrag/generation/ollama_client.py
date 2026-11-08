"""Ollama chat client with the parameters PLAN §2 requires on every request:
temperature=0, presence_penalty=0, think=false, explicit num_ctx and num_predict."""
from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from vkrag.config import load_config


@dataclass
class OllamaResult:
    content: str
    done_reason: str | None
    prompt_eval_count: int | None
    eval_count: int | None
    latency_s: float
    model: str


class Ollama:
    def __init__(self, cfg: dict | None = None, timeout: float = 600.0):
        self.cfg = cfg or load_config()["ollama"]
        self.http = httpx.Client(base_url=self.cfg["host"], timeout=timeout)

    def chat(self, messages: list[dict], num_predict: int, keep_alive: str | int = "10m") -> OllamaResult:
        c = self.cfg
        body = {
            "model": c["model"],
            "messages": messages,
            "stream": False,
            "think": c["think"],
            "keep_alive": keep_alive,
            "options": {
                "temperature": c["temperature"],
                "presence_penalty": c["presence_penalty"],
                "num_ctx": c["num_ctx"],
                "num_predict": num_predict,
            },
        }
        t0 = time.perf_counter()
        r = self.http.post("/api/chat", json=body)
        r.raise_for_status()
        j = r.json()
        content = j["message"]["content"]
        if "<think>" in content or (j["message"].get("thinking") or "").strip():
            raise RuntimeError("thinking output present although think=false")
        return OllamaResult(content=content, done_reason=j.get("done_reason"), prompt_eval_count=j.get("prompt_eval_count"),
                            eval_count=j.get("eval_count"), latency_s=round(time.perf_counter() - t0, 3), model=j.get("model"))

    def unload(self) -> None:
        self.http.post("/api/generate", json={"model": self.cfg["model"], "keep_alive": 0})

    def digest(self) -> str | None:
        tags = self.http.get("/api/tags").json()["models"]
        return next((m["digest"] for m in tags if m["name"].split(":")[0] == self.cfg["model"].split(":")[0]), None)
