"""Stage 3b: acceptable_vuids (multiple gold, PLAN §4 Stage 3, §9.2 item 3).

For every answerable question the first 10 VU chunks outside the gold equivalence class in the
`rrf_rerank` ranking of the run are checked by the judge (OpenRouter, `openrouter.judge`):
"Does the candidate rule answer the question as fully and correctly as the gold rule?".
Approved VUs become acceptable_vuids; their classes are added to gold_chunk_ids with relevance 2.
Questions with more than 2 approved VUs are flagged `ambiguous` for manual review.
Judge calls are cached in generation_log/<sample>_acceptable.jsonl by (qid, candidate, prompt hash, model).
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from vkrag.config import PROCESSED, ROOT, load_config
from vkrag.questions.prepare import GLOG

PROMPT = Path(__file__).resolve().parents[1] / "generation" / "prompts" / "judge_acceptable.md"
TOP_N = 10
MAX_ACCEPTABLE = 2
SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "acceptable",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"equivalent": {"type": "boolean"}, "reason": {"type": "string"}},
            "required": ["equivalent", "reason"],
            "additionalProperties": False,
        },
    },
}


def prompt() -> tuple[str, str]:
    t = PROMPT.read_text(encoding="utf-8").strip()
    return t, hashlib.sha256(t.encode()).hexdigest()[:12]


def candidates(sample: str, run_id: str) -> dict[str, list[str]]:
    from vkrag.retrieval.run import config_hash, load_questions

    cfg = load_config()
    h = config_hash("rrf_rerank", cfg)
    qs = {q["qid"]: q for q in load_questions(sample) if q["stratum"] != "unanswerable"}
    vus = {}
    for line in open(PROCESSED / "vuids.jsonl", encoding="utf-8"):
        v = json.loads(line)
        vus[v["vuid"]] = v
    out: dict[str, list[str]] = {}
    for line in open(ROOT / "runs" / run_id / "retrieved.jsonl", encoding="utf-8"):
        r = json.loads(line)
        q = qs.get(r["qid"])
        if not q or r["config"] != "rrf_rerank" or r["config_hash"] != h or r["question_hash"] != q["question_hash"]:
            continue
        gold_cls = vus[q["vuid"]]["equiv_class_id"]
        seen_cls, cand = set(), []
        for d, _ in r["ranked"]:
            v = vus.get(d)
            if not v or v["equiv_class_id"] == gold_cls or v["equiv_class_id"] in seen_cls:
                continue
            seen_cls.add(v["equiv_class_id"])
            cand.append(d)
            if len(cand) == TOP_N:
                break
        out[q["qid"]] = cand
    missing = set(qs) - set(out)
    if missing:
        raise RuntimeError(f"no current rrf_rerank ranking for {len(missing)} questions; run `vkrag retrieve` first")
    return out


def user_message(q: dict, gold_text: str, cand_text: str) -> str:
    return (
        f"Question:\n{q['question']}\n\nReference answer:\n{q['reference_answer']}\n\n"
        f"Gold rule:\n{gold_text}\n\nCandidate rule:\n{cand_text}"
    )


def _cache_path(sample: str) -> Path:
    return GLOG / f"{sample}_acceptable.jsonl"


def _cached(sample: str) -> dict[tuple, dict]:
    p = _cache_path(sample)
    out = {}
    if p.exists():
        for line in open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            out[(r["qid"], r["candidate"], r["prompt_hash"], r["judge_model"])] = r
    return out


def run(sample: str, run_id: str, dry_run: bool = False, max_usd: float | None = None, limit: int | None = None) -> dict:
    from vkrag.generation.openrouter import OpenRouter, role
    from vkrag.retrieval.run import load_questions

    qs = {q["qid"]: q for q in load_questions(sample)}
    cands = candidates(sample, run_id)
    chunk_text = {}
    for line in open(PROCESSED / "chunks.jsonl", encoding="utf-8"):
        c = json.loads(line)
        if c["type"] == "vu":
            chunk_text[c["chunk_id"]] = c["llm_text"]
    system, ph = prompt()
    rc = role("judge")
    cache = _cached(sample)
    todo = [(qid, c) for qid, cs in cands.items() for c in cs if (qid, c, ph, rc["model"]) not in cache]
    o = OpenRouter()
    m = o.model_info(rc["model"]) or {}
    price = m.get("pricing", {})
    real = [r for r in cache.values() if r.get("prompt_tokens") and r.get("cost_usd") is not None]
    if len(real) >= 5:  # measured usage of earlier calls (chars/3.5 overestimates by ~1.5x)
        in_tok = len(todo) * sum(r["prompt_tokens"] for r in real) / len(real)
        out_tok = int(len(todo) * sum(r["completion_tokens"] for r in real) / len(real))
    else:
        in_tok = sum(len(system) + len(user_message(qs[qid], chunk_text[qs[qid]["vuid"]], chunk_text[c])) for qid, c in todo) / 3.5
        out_tok = len(todo) * 200
    est = in_tok * float(price.get("prompt", 0)) + out_tok * float(price.get("completion", 0))
    stats = {
        "questions": len(cands),
        "candidates": sum(map(len, cands.values())),
        "todo_calls": len(todo),
        "est_input_tokens": int(in_tok),
        "est_output_tokens": out_tok,
        "est_usd": round(est, 4),
        "price_per_token": {k: price.get(k) for k in ("prompt", "completion")},
    }
    if dry_run or not todo:
        return stats
    if limit:
        todo = todo[:limit]
    elif max_usd is not None and est > max_usd:
        raise RuntimeError(f"estimated ${est:.2f} > limit ${max_usd:.2f}")
    spent = 0.0
    with open(_cache_path(sample), "a", encoding="utf-8") as f:
        for i, (qid, c) in enumerate(todo):
            q = qs[qid]
            msgs = [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message(q, chunk_text[q["vuid"]], chunk_text[c])},
            ]
            v, r = None, None
            for _ in range(3):
                r = o.chat(rc, msgs, response_format=SCHEMA)
                spent += r.cost_usd or 0.0
                try:
                    v = json.loads(r.content or "")
                    break
                except json.JSONDecodeError:
                    continue
            if r.model and not r.model.startswith(rc["model"].split(":")[0].rsplit("-", 1)[0]):
                raise RuntimeError(f"judge model mismatch: {r.model}")
            rec = {
                "qid": qid,
                "candidate": c,
                "rank": cands[qid].index(c) + 1,
                "prompt_hash": ph,
                "judge_model": rc["model"],
                "actual_model": r.model,
                "provider": r.provider,
                "equivalent": None if v is None else v["equivalent"],
                "reason": None if v is None else v["reason"],
                "cost_usd": r.cost_usd,
                "prompt_tokens": r.usage.get("prompt_tokens"),
                "completion_tokens": r.usage.get("completion_tokens"),
                "reasoning_tokens": r.reasoning_tokens,
                "finish_reason": r.finish_reason,
                "latency_s": r.latency_s,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if max_usd is not None and spent > max_usd:
                stats["stopped_at_budget"] = i + 1
                break
    stats["spent_usd"] = round(spent, 4)
    return stats


def apply(sample: str, run_id: str) -> dict:
    """Write acceptable_vuids and the extended gold into the frozen question file (question texts and
    hashes are untouched), set gold_final, update the manifest."""
    from vkrag.questions.freeze import out_path

    system, ph = prompt()
    model = load_config()["openrouter"]["judge"]["model"]
    cache = _cached(sample)
    cands = candidates(sample, run_id)
    by_class = defaultdict(list)
    cls = {}
    for line in open(PROCESSED / "vuids.jsonl", encoding="utf-8"):
        v = json.loads(line)
        by_class[v["equiv_class_id"]].append(v["vuid"])
        cls[v["vuid"]] = v["equiv_class_id"]
    path = out_path(sample)
    qs = [json.loads(l) for l in open(path, encoding="utf-8")]
    missing, ambiguous, n_acc = 0, [], 0
    for q in qs:
        if q["stratum"] == "unanswerable":
            continue
        verdicts = [cache.get((q["qid"], c, ph, model)) for c in cands[q["qid"]]]
        missing += sum(v is None or v["equivalent"] is None for v in verdicts)
        acc = [v["candidate"] for v in verdicts if v and v["equivalent"]]
        q["acceptable_vuids"] = acc
        gold = {d: g for d, g in q["gold_chunk_ids"].items()}
        for a in acc:
            for member in by_class[cls[a]]:
                gold[member] = max(gold.get(member, 0), 2)
        q["gold_chunk_ids"] = dict(sorted(gold.items(), key=lambda kv: (-kv[1], kv[0])))
        q["ambiguous"] = len(acc) > MAX_ACCEPTABLE
        q["gold_final"] = missing == 0
        n_acc += bool(acc)
        if q["ambiguous"]:
            ambiguous.append(q["qid"])
    if missing:
        return {"missing_verdicts": missing, "written": False}
    text = "".join(json.dumps(q, ensure_ascii=False) + "\n" for q in qs)
    path.write_text(text, encoding="utf-8")
    mp = path.with_suffix(".manifest.json")
    man = json.load(open(mp, encoding="utf-8"))
    man.update(
        {
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "gold_final": True,
            "stage": "3b",
            "acceptable": {
                "questions_with_acceptable": n_acc,
                "ambiguous": ambiguous,
                "judge_model": model,
                "prompt_hash": ph,
                "run_id": run_id,
                "top_n": TOP_N,
            },
        }
    )
    mp.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    return {"written": True, "questions_with_acceptable": n_acc, "ambiguous": ambiguous, "sha256": man["sha256"]}
