"""Phase D (PLAN §7.2): LLM judge over the phase-C answers -> runs/<run_id>/judgments.jsonl, then
automatic checks and the merged per-answer table runs/<run_id>/scores.jsonl + generation_metrics.json.

- correctness: every configuration, without the context; the answer is masked (eval/masking.py);
  inputs: question, type, reference answer, gold VU text and the texts of acceptable_vuids
  (an equivalence class has identical raw text by construction, so the gold text represents it);
  for unanswerable questions the spec evidence and the rationale of the false premise;
- faithfulness: RAG configurations only; context + question + the unmasked answer (the context
  already reveals the configuration, and citations [n] are needed to check grounding);
- calls are shuffled (seed); cached by (answer key, kind, prompt hash, judge model, judge_repeat_idx);
- missing answers are not judged: incorrect, abstained=false, missing=true (skip policy, Stage 6);
- a judgment that fails 3 times is recorded with `failed=true` and treated the same way.
"""
from __future__ import annotations

import hashlib
import json
import random
import statistics
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from vkrag.config import PROCESSED, ROOT, load_config
from vkrag.eval.masking import mask

PROMPTS = Path(__file__).resolve().parents[1] / "generation" / "prompts"
KINDS = ("correctness", "faithfulness")
SCHEMAS = {
    "correctness": {"type": "object", "additionalProperties": False,
                    "required": ["correctness", "abstained", "hallucination", "scenario_other_violation", "reason"],
                    "properties": {"correctness": {"type": "string", "enum": ["correct", "partial", "incorrect"]},
                                   "abstained": {"type": "boolean"}, "hallucination": {"type": "boolean"},
                                   "scenario_other_violation": {"type": "boolean"}, "reason": {"type": "string"}}},
    "faithfulness": {"type": "object", "additionalProperties": False,
                     "required": ["faithfulness", "self_knowledge", "reason"],
                     "properties": {"faithfulness": {"type": "string", "enum": ["supported", "contradicts", "not_grounded"]},
                                    "self_knowledge": {"type": "boolean"}, "reason": {"type": "string"}}},
}
SCORE = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}
OUTPUT_TOKENS_EST = 500  # reasoning medium + JSON; refined from cached calls once available


def prompt(kind: str) -> tuple[str, str]:
    t = (PROMPTS / f"judge_{kind}.md").read_text(encoding="utf-8").strip()
    return t, hashlib.sha256(t.encode()).hexdigest()[:12]


def _h(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def _jsonl(path: Path) -> list[dict]:
    out = []
    if path.exists():
        for line in open(path, encoding="utf-8"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a truncated last line is dropped
    return out


def current_answers(sample: str, run_id: str) -> tuple[list[dict], dict[str, dict]]:
    """Latest answer per (qid, config, answerer, repeat_idx) whose question hash is current."""
    from vkrag.generation.answer import gen_questions

    qs = {q["qid"]: q for q in gen_questions(sample)}
    latest: dict[tuple, dict] = {}
    for r in _jsonl(ROOT / "runs" / run_id / "answers.jsonl"):
        q = qs.get(r["qid"])
        if q and q["question_hash"] == r["question_hash"]:
            latest[(r["qid"], r["config"], r["answerer"], r["repeat_idx"])] = r
    return list(latest.values()), qs


def vu_texts() -> dict[str, str]:
    out = {}
    for line in open(PROCESSED / "chunks.jsonl", encoding="utf-8"):
        c = json.loads(line)
        if c["type"] == "vu":
            out[c["chunk_id"]] = c["index_text"]
    return out


def correctness_message(q: dict, masked_answer: str, vtext: dict[str, str]) -> str:
    unans = q["stratum"] == "unanswerable"
    qtype = "unanswerable (false premise or non-existent entity)" if unans else q["answer_type"]
    parts = [f"Question type: {qtype}", f"Question:\n{q['question']}", f"Reference answer:\n{q['reference_answer']}"]
    if q.get("answer_type") == "yes_no" and q.get("expected_verdict"):
        parts.append(f"Expected verdict: {q['expected_verdict']}")
    if unans:
        parts.append(f"Why the premise is false:\n{q.get('rationale', '')}")
        ev = [e["text"] for e in q.get("spec_evidence") or []]
        if ev:
            parts.append("Specification text:\n" + "\n".join(f"- {t}" for t in ev))
    else:
        rules = [vtext[q["vuid"]]] + [vtext[a] for a in q.get("acceptable_vuids") or [] if a in vtext]
        parts.append("Specification rule(s):\n" + "\n\n".join(rules))
    parts.append(f"Answer to grade:\n{masked_answer}")
    return "\n\n".join(parts)


def faithfulness_message(q: dict, answer: str, ctx: list[str], chunks: dict) -> str:
    from vkrag.generation.answer import render_context

    return f"Context:\n{render_context(ctx, chunks)}\n\nQuestion:\n{q['question']}\n\nAnswer:\n{answer}"


def build_calls(answers: list[dict], qs: dict, judge_repeat_idx: int = 0) -> list[dict]:
    from vkrag.generation.answer import load_chunks

    cfg = load_config()
    model = cfg["openrouter"]["judge"]["model"]
    vtext, chunks = vu_texts(), load_chunks()
    prompts = {k: prompt(k) for k in KINDS}
    calls = []
    for a in answers:
        if a["missing"]:
            continue
        q = qs[a["qid"]]
        masked, marker = mask(a["answer"])
        base = {"answer_key": a["key"], "qid": a["qid"], "config": a["config"], "answerer": a["answerer"],
                "repeat_idx": a["repeat_idx"], "judge_repeat_idx": judge_repeat_idx, "judge_model": model}
        system, ph = prompts["correctness"]
        calls.append(base | {"kind": "correctness", "prompt_hash": ph, "mask_marker": marker,
                             "messages": [{"role": "system", "content": system},
                                          {"role": "user", "content": correctness_message(q, masked, vtext)}]})
        if a["config"] != "closed" and a.get("context"):
            system, ph = prompts["faithfulness"]
            calls.append(base | {"kind": "faithfulness", "prompt_hash": ph,
                                 "messages": [{"role": "system", "content": system},
                                              {"role": "user", "content": faithfulness_message(q, a["answer"], a["context"], chunks)}]})
    for c in calls:
        c["input_hash"] = _h(c["messages"])  # masking / context changes invalidate the cache
        c["key"] = _h({k: c[k] for k in ("answer_key", "kind", "prompt_hash", "input_hash", "judge_model", "judge_repeat_idx")})
    random.Random(cfg["seed"] + judge_repeat_idx).shuffle(calls)  # blinding: no config/model order
    return calls


def estimate(todo: list[dict], cached: list[dict]) -> dict:
    from vkrag import tokens
    from vkrag.generation.openrouter import OpenRouter

    rc = load_config()["openrouter"]["judge"]
    price = (OpenRouter().model_info(rc["model"]) or {}).get("pricing", {})
    out = {}
    for kind in KINDS:
        js = [c for c in todo if c["kind"] == kind]
        if not js:
            continue
        real = [r for r in cached if r["kind"] == kind and r.get("prompt_tokens")]
        tin = sum(tokens.count(m["content"], "qwen") + 8 for c in js for m in c["messages"])
        per_out = (sum(r["completion_tokens"] for r in real) / len(real)) if len(real) >= 5 else OUTPUT_TOKENS_EST
        tout = int(per_out * len(js))
        out[kind] = {"calls": len(js), "input_tokens": tin, "output_tokens_est": tout,
                     "est_usd": round(tin * float(price.get("prompt", 0)) + tout * float(price.get("completion", 0)), 4)}
    out["total_usd"] = round(sum(v["est_usd"] for v in out.values()), 4)
    out["price"] = {k: price.get(k) for k in ("prompt", "completion")}
    return out


def run(sample: str, run_id: str, dry_run: bool = False, max_usd: float | None = None, limit: int | None = None,
        judge_repeat_idx: int = 0, configs: tuple[str, ...] | None = None, workers: int = 8) -> dict:
    from vkrag.generation.openrouter import OpenRouter

    rdir = ROOT / "runs" / run_id
    out_file, usage_file = rdir / "judgments.jsonl", rdir / "usage.jsonl"
    answers, qs = current_answers(sample, run_id)
    if configs:
        answers = [a for a in answers if a["config"] in configs]
    calls = build_calls(answers, qs, judge_repeat_idx)
    cached = _jsonl(out_file)
    have = {r["key"] for r in cached if not r.get("failed")}
    todo = [c for c in calls if c["key"] not in have]
    stats = {"answers": len(answers), "missing_answers": sum(a["missing"] for a in answers), "calls": len(calls),
             "todo": len(todo), "estimate": estimate(todo, cached) if todo else {}}
    if dry_run or not todo:
        return stats
    if limit:
        todo = todo[:limit]
    elif max_usd is not None and stats["estimate"]["total_usd"] > max_usd:
        raise RuntimeError(f"estimated ${stats['estimate']['total_usd']:.2f} > limit ${max_usd:.2f}")
    rc = load_config()["openrouter"]["judge"]
    o = OpenRouter()
    lock = threading.Lock()
    state = {"spent": 0.0, "failed": 0, "written": 0, "stop": False}

    def one(c: dict, f, uf) -> None:
        if state["stop"]:
            return
        schema = {"type": "json_schema", "json_schema": {"name": c["kind"], "strict": True, "schema": SCHEMAS[c["kind"]]}}
        v, r, err = None, None, None
        for attempt in range(3):
            try:
                r = o.chat(rc, c["messages"], response_format=schema)
            except Exception as e:  # noqa: BLE001
                r, err = None, f"{type(e).__name__}: {str(e)[:200]}"
            if r is not None:
                if not (r.model or "").startswith(rc["model"]):
                    state["stop"] = True
                    raise RuntimeError(f"judge model mismatch: {r.model}")
                try:
                    v = json.loads(r.content or "")
                    missing_fields = set(SCHEMAS[c["kind"]]["required"]) - set(v)
                    if missing_fields:
                        raise ValueError(f"missing {missing_fields}")
                except (json.JSONDecodeError, ValueError) as e:
                    v, err = None, f"schema: {e}"
            with lock:
                if r is not None:
                    state["spent"] += r.cost_usd or 0.0
                uf.write(json.dumps({"ts": round(time.time(), 3), "phase": "D", "kind": c["kind"], "qid": c["qid"],
                                     "config": c["config"], "model": rc["model"], "answerer": c["answerer"],
                                     "repeat_idx": c["repeat_idx"], "attempt": attempt, "error": None if v else err,
                                     "prompt_tokens": r.usage.get("prompt_tokens") if r else None,
                                     "completion_tokens": r.usage.get("completion_tokens") if r else None,
                                     "reasoning_tokens": r.reasoning_tokens if r else None,
                                     "latency_s": r.latency_s if r else None, "provider": r.provider if r else None,
                                     "finish_reason": r.finish_reason if r else None,
                                     "cost_usd": r.cost_usd if r else None,
                                     "cached_tokens": r.cached_tokens if r else None}) + "\n")
                uf.flush()
            if v is not None:
                break
            time.sleep(2 * (attempt + 1))
        rec = {k: c[k] for k in ("key", "input_hash", "answer_key", "qid", "config", "answerer", "repeat_idx", "judge_repeat_idx",
                                 "kind", "prompt_hash", "judge_model")}
        rec.update({"verdict": v, "failed": v is None, "error": None if v else err, "mask_marker": c.get("mask_marker"),
                    "actual_model": r.model if r else None, "provider": r.provider if r else None,
                    "cost_usd": r.cost_usd if r else None,
                    "prompt_tokens": r.usage.get("prompt_tokens") if r else None,
                    "completion_tokens": r.usage.get("completion_tokens") if r else None,
                    "reasoning_tokens": r.reasoning_tokens if r else None})
        with lock:
            state["failed"] += v is None
            state["written"] += 1
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if max_usd is not None and state["spent"] > max_usd:
                state["stop"] = True
                stats["stopped_at_budget"] = state["written"]

    with open(out_file, "a", encoding="utf-8") as f, open(usage_file, "a", encoding="utf-8") as uf, \
            ThreadPoolExecutor(max_workers=workers) as ex:
        for fut in [ex.submit(one, c, f, uf) for c in todo]:
            fut.result()
    return stats | {"written": state["written"], "failed": state["failed"], "spent_usd": round(state["spent"], 4)}


# ---------------------------------------------------------------- merge and metrics

def merge(sample: str, run_id: str, judge_repeat_idx: int = 0) -> list[dict]:
    """One row per answer: judge verdicts, automatic checks, score -> runs/<run_id>/scores.jsonl."""
    from vkrag.eval.autocheck import Checker

    rdir = ROOT / "runs" / run_id
    answers, qs = current_answers(sample, run_id)
    valid = {c["key"] for c in build_calls(answers, qs, judge_repeat_idx)}  # current prompts, inputs, model
    j = {}
    for r in _jsonl(rdir / "judgments.jsonl"):
        if r["key"] in valid:
            j[(r["answer_key"], r["kind"])] = r
    chk = Checker()
    rows = []
    for a in answers:
        q = qs[a["qid"]]
        row = {k: a[k] for k in ("qid", "config", "answerer", "repeat_idx")}
        row.update({"stratum": q["stratum"], "style": q["style"], "answer_type": q.get("answer_type"),
                    "entity": q.get("entity"), "answerable": q["stratum"] != "unanswerable", "missing": a["missing"],
                    "cost_usd": a.get("cost_usd"), "latency_s": a.get("latency_s"),
                    "prompt_tokens": a.get("prompt_tokens"), "completion_tokens": a.get("completion_tokens"),
                    "reasoning_tokens": a.get("reasoning_tokens"), "answer_chars": len(a["answer"] or "")})
        jc, jf = j.get((a["key"], "correctness")), j.get((a["key"], "faithfulness"))
        if a["missing"] or (jc and jc["failed"]):
            row.update({"correctness": "incorrect", "abstained": False, "hallucination": None, "score": 0.0,
                        "judge_failed": bool(jc and jc["failed"])})
        elif jc:
            v = jc["verdict"]
            row.update({"correctness": v["correctness"], "abstained": v["abstained"], "hallucination": v["hallucination"],
                        "scenario_other_violation": v["scenario_other_violation"], "score": SCORE[v["correctness"]],
                        "judge_reason": v["reason"], "mask_marker": jc.get("mask_marker"), "judge_failed": False})
        else:
            row["correctness"] = None  # not judged yet
        if jf and not jf["failed"]:
            row.update({"faithfulness": jf["verdict"]["faithfulness"], "self_knowledge": jf["verdict"]["self_knowledge"]})
        if not a["missing"]:
            row.update(chk.check(a["answer"], q))
        rows.append(row)
    with open(rdir / "scores.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows


def _rate(rows: list[dict], key: str, pred=lambda v: bool(v)) -> float | None:
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(sum(pred(v) for v in vals) / len(vals), 3) if vals else None


def metrics(rows: list[dict]) -> dict:
    """Per (answerer, config): answerable and unanswerable questions separately (point estimates; CIs in Stage 7.4)."""
    groups = defaultdict(list)
    for r in rows:
        if r.get("correctness") is not None:
            groups[(r["answerer"], r["config"], "answerable" if r["answerable"] else "unanswerable")].append(r)
    out = {}
    for (a, c, part), rs in sorted(groups.items()):
        answered = [r for r in rs if not r["abstained"] and not r["missing"]]
        m = {"n": len(rs), "score": round(statistics.mean(r["score"] for r in rs), 3),
             "correct": _rate(rs, "correctness", lambda v: v == "correct"),
             "abstain": _rate(rs, "abstained"), "missing": _rate(rs, "missing"),
             "selective_accuracy": round(statistics.mean(r["score"] for r in answered), 3) if answered else None,
             "coverage": round(len(answered) / len(rs), 3),
             "hallucination": _rate(rs, "hallucination"),
             "fabricated_identifier": _rate(rs, "fabricated_identifier"), "outdated_identifier": _rate(rs, "outdated_identifier"),
             "fabricated_vuid": _rate(rs, "fabricated_vuid"), "citation_correct": _rate(rs, "citation_correct"),
             "cites_vuid": _rate([r for r in rs if not r["missing"]], "cited_vuids"),
             "faithful_supported": _rate(rs, "faithfulness", lambda v: v == "supported"),
             "self_knowledge": _rate(rs, "self_knowledge"), "mask_marker": _rate(rs, "mask_marker"),
             "verdict_match": _rate(rs, "verdict_match"), "verdict_conditional": _rate(rs, "verdict", lambda v: v == "conditional"),
             "answer_chars_median": statistics.median(r["answer_chars"] for r in rs),
             "latency_s_p50": round(statistics.median([r["latency_s"] for r in rs if r.get("latency_s")] or [0]), 2)}
        costs = [r["cost_usd"] for r in rs if r.get("cost_usd") is not None]
        if costs:
            m["cost_per_question"] = round(sum(costs) / len(rs), 6)
            m["cost_per_correct"] = round(sum(costs) / sum(r["score"] for r in rs), 6) if sum(r["score"] for r in rs) else None
            m["tokens_in_mean"] = round(statistics.mean(r["prompt_tokens"] or 0 for r in rs))
            m["tokens_out_mean"] = round(statistics.mean(r["completion_tokens"] or 0 for r in rs))
        out[f"{a}|{c}|{part}"] = m
    return out


def table(m: dict) -> str:
    cols = ("n", "score", "correct", "abstain", "selective_accuracy", "hallucination", "fabricated_identifier",
            "fabricated_vuid", "citation_correct", "faithful_supported", "self_knowledge", "missing")
    lines = ["| answerer | config | part | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 3)]
    for k, v in m.items():
        lines.append("| " + " | ".join(k.split("|")) + " | " + " | ".join("" if v.get(c) is None else str(v[c]) for c in cols) + " |")
    return "\n".join(lines)
