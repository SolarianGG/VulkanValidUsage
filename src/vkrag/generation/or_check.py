"""Stage 0 / PLAN §9.4: OpenRouter checks for the answerer and the judge.

Checks, per candidate provider endpoint: routing with `allow_fallbacks: false`,
`require_parameters: true`, `data_collection: deny`; the actual model and provider in the
response; `usage.cost`; reasoning tokens with reasoning disabled (answerer); `response_format`
json_schema (judge); repeat determinism at temperature 0. Writes reports/openrouter_check.json.
A full run costs well under $0.05.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from vkrag.config import ROOT
from vkrag.generation.openrouter import OpenRouter, role

ANSWER_Q = [
    {"role": "system", "content": "You are an expert on the Vulkan API specification. Answer concisely."},
    {"role": "user", "content": "Can vkCmdDraw be recorded outside a render pass instance? Start your answer with Yes or No."},
]
JUDGE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "correctness",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "correctness": {"type": "string", "enum": ["correct", "partial", "incorrect"]},
                "abstained": {"type": "boolean"},
                "hallucination": {"type": "boolean"},
                "scenario_other_violation": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            "required": ["correctness", "abstained", "hallucination", "scenario_other_violation", "reason"],
            "additionalProperties": False,
        },
    },
}
JUDGE_MSG = [
    {"role": "system", "content": "You grade answers about the Vulkan specification. Reply with JSON only."},
    {
        "role": "user",
        "content": (
            "Question: Can vkCmdDraw be recorded outside a render pass instance?\n"
            "Reference answer: No. vkCmdDraw must be recorded inside a render pass instance (it is an action command "
            "with the 'Inside' render pass scope).\n"
            "Model answer: No, it must only be called inside a render pass instance; also it requires Vulkan 1.3.\n"
            "Grade correctness (correct|partial|incorrect), abstained, hallucination, scenario_other_violation, reason (<= 60 words)."
        ),
    },
]


def _row(res, extra=None) -> dict:
    d = {
        "model": res.model,
        "provider": res.provider,
        "finish_reason": res.finish_reason,
        "prompt_tokens": res.usage.get("prompt_tokens"),
        "completion_tokens": res.usage.get("completion_tokens"),
        "reasoning_tokens": res.reasoning_tokens,
        "cached_tokens": res.cached_tokens,
        "cost_usd": res.cost_usd,
        "latency_s": res.latency_s,
        "content": (res.content or "")[:400],
        "has_reasoning_text": bool(res.reasoning),
    }
    d.update(extra or {})
    return d


def run(answerer_providers: list[str], judge_providers: list[str]) -> dict:
    o = OpenRouter()
    out: dict = {"date": datetime.now(UTC).isoformat(timespec="seconds")}
    k = o.key_info()
    out["key"] = {x: k.get(x) for x in ("limit", "limit_remaining", "usage", "limit_reset", "is_free_tier")}
    for name, provs in (("answerer_remote", answerer_providers), ("judge", judge_providers)):
        rc = role(name)
        out[name] = {"model": rc["model"], "config_provider": rc["provider"], "runs": []}
        for p in provs:
            try:
                if name == "answerer_remote":
                    a = o.chat(rc, ANSWER_Q, max_tokens=128, provider_order=[p])
                    b = o.chat(rc, ANSWER_Q, max_tokens=128, provider_order=[p])
                    row = _row(a, {"requested": p, "repeat_identical": a.content == b.content, "cost_second_usd": b.cost_usd})
                else:
                    a = o.chat(rc, JUDGE_MSG, response_format=JUDGE_SCHEMA, provider_order=[p])
                    try:
                        parsed = json.loads(a.content or "")
                        ok = set(parsed) == set(JUDGE_SCHEMA["json_schema"]["schema"]["required"])
                    except json.JSONDecodeError:
                        parsed, ok = None, False
                    row = _row(a, {"requested": p, "json_ok": ok, "parsed": parsed})
                g = o.generation(a.gen_id) if a.gen_id else None
                if g:
                    row["generation"] = {
                        x: g.get(x)
                        for x in (
                            "provider_name",
                            "model",
                            "total_cost",
                            "native_tokens_prompt",
                            "native_tokens_completion",
                            "native_tokens_reasoning",
                            "finish_reason",
                        )
                    }
                row["model_matches"] = (a.model or "").startswith(rc["model"].split(":")[0]) or a.model == o.model_info(rc["model"])[
                    "canonical_slug"
                ]
            except Exception as e:  # noqa: BLE001 - record the routing failure
                row = {"requested": p, "error": str(e)[:600]}
            out[name]["runs"].append(row)
            print(
                name,
                p,
                json.dumps(
                    {
                        x: row.get(x)
                        for x in ("provider", "model", "cost_usd", "reasoning_tokens", "latency_s", "json_ok", "repeat_identical", "error")
                    }
                ),
            )
    k2 = o.key_info()
    out["spent_usd"] = round((k2.get("usage") or 0) - (k.get("usage") or 0), 6)
    (ROOT / "reports" / "openrouter_check.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out
