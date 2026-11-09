"""Choice of the pinned OpenRouter provider for `answerer_remote` (PLAN §9.1: the provider with the lowest
error share on the pilot). Every eligible endpoint (quantization in the config list) answers the same
real pilot prompts (rrf_rerank contexts); errors, latency and cost go to reports/remote_provider_probe.json.

Run: uv run python -m vkrag.generation.provider_probe [n_prompts]
"""
from __future__ import annotations

import json
import sys
import time

from vkrag.config import ROOT, load_config


def main(n: int = 6) -> None:
    from vkrag.generation.answer import jobs
    from vkrag.generation.openrouter import OpenRouter

    cfg = load_config()
    rc = cfg["openrouter"]["answerer_remote"]
    js, _ = jobs("pilot", "pilot", ("rrf_rerank",), ("remote",), limit=n)
    o = OpenRouter(retries=0)
    eps = [e for e in o.endpoints(rc["model"]) if e.get("quantization") in rc["provider"]["quantizations"]]
    out = {"date": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": rc["model"], "prompts": len(js), "providers": []}
    for e in eps:
        slug = e["tag"]
        row = {"provider": e["provider_name"], "slug": slug, "quantization": e.get("quantization"),
               "pricing": e.get("pricing"), "ok": 0, "errors": [], "latency_s": [], "cost_usd": 0.0, "answers": []}
        for j in js:
            try:
                r = o.chat(rc, j["messages"], provider_order=[slug])
                ok = bool((r.content or "").strip()) and r.finish_reason != "length"
                row["ok"] += ok
                row["latency_s"].append(r.latency_s)
                row["cost_usd"] += r.cost_usd or 0
                row["answers"].append({"qid": j["qid"], "provider": r.provider, "model": r.model,
                                       "completion_tokens": r.usage.get("completion_tokens"), "text": (r.content or "")[:200]})
            except Exception as ex:  # noqa: BLE001
                row["errors"].append(str(ex)[:200])
        row["latency_s_median"] = sorted(row["latency_s"])[len(row["latency_s"]) // 2] if row["latency_s"] else None
        print(row["slug"], "ok", row["ok"], "/", len(js), "median", row["latency_s_median"], "cost", round(row["cost_usd"], 6))
        out["providers"].append(row)
    (ROOT / "reports" / "remote_provider_probe.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 6)
