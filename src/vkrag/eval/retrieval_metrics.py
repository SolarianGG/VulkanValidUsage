"""Retrieval metrics (PLAN §7.1) over runs/<run_id>/retrieved.jsonl, answerable questions only.

strict@k  the gold VU chunk of this entity is in the top k
class@k   any VU chunk of the gold equivalence class or of an acceptable_vuids class (relevance >= 2)
soft@k    any part of the parent section
MRR@10    first chunk with relevance >= 2
nDCG@10   graded relevance from gold_chunk_ids (3 / 2 / 1)
For oracle configurations the context list is the ranking.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict

from vkrag.config import ROOT, load_config


def metrics_for(ranking: list[str], q: dict, parent_parts: set[str], ks: list[int], ideal: list[int] | None = None) -> dict:
    """`ideal`: relevance grades of the ideal ranking; by default all gold grades (with collapsed
    rankings pass one grade per equivalence class, see `collapsed_ideal`)."""
    gold = q["gold_chunk_ids"]
    out = {}
    for k in ks:
        top = ranking[:k]
        out[f"strict@{k}"] = float(q["vuid"] in top)
        out[f"class@{k}"] = float(any(gold.get(d, 0) >= 2 for d in top))
        out[f"soft@{k}"] = float(any(d in parent_parts for d in top))
    rr = 0.0
    for i, d in enumerate(ranking[:10], 1):
        if gold.get(d, 0) >= 2:
            rr = 1.0 / i
            break
    out["mrr@10"] = rr
    dcg = sum((2 ** gold.get(d, 0) - 1) / math.log2(i + 1) for i, d in enumerate(ranking[:10], 1))
    ideal = sorted(ideal if ideal is not None else gold.values(), reverse=True)[:10]
    idcg = sum((2**g - 1) / math.log2(i + 1) for i, g in enumerate(ideal, 1))
    out["ndcg@10"] = dcg / idcg if idcg else 0.0
    return out


def collapsed_ideal(gold: dict[str, int], chunks: dict[str, dict]) -> list[int]:
    best: dict[str, int] = {}
    for d, g in gold.items():
        c = chunks.get(d)
        k = c["equiv_class_id"] if c and c["type"] == "vu" else d
        best[k] = max(best.get(k, 0), g)
    return list(best.values())


def evaluate(sample: str, run_id: str) -> dict:
    from vkrag.retrieval.core import Corpus
    from vkrag.retrieval.run import load_questions

    ks = load_config()["retrieval"]["k_eval"]
    qs = {q["qid"]: q for q in load_questions(sample) if q["stratum"] != "unanswerable"}
    corpus = Corpus()
    per: dict[str, list[dict]] = defaultdict(list)
    rows = []
    from vkrag.retrieval.run import config_hash

    cfg = load_config()
    current: dict[str, str] = {}
    for line in open(ROOT / "runs" / run_id / "retrieved.jsonl", encoding="utf-8"):
        r = json.loads(line)
        q = qs.get(r["qid"])
        if r["config"] not in current:
            current[r["config"]] = config_hash(r["config"], cfg)
        if not q or r["question_hash"] != q["question_hash"] or r["config_hash"] != current[r["config"]]:
            continue  # stale record (other parameters) or unanswerable
        ranking = [d for d, _ in r["ranked"]] if r["ranked"] is not None else r["context"]
        parent = set(corpus.sections.get(corpus.chunks[q["vuid"]]["section_id"], []))
        ideal = collapsed_ideal(q["gold_chunk_ids"], corpus.chunks) if cfg["retrieval"].get("collapse_classes") else None
        m = metrics_for(ranking, q, parent, ks, ideal)
        ctx_types = [corpus.chunks[d]["type"] for d in r["context"]]
        m["ctx_vu_share"] = ctx_types.count("vu") / len(ctx_types) if ctx_types else 0.0
        m["ctx_strict"] = float(q["vuid"] in r["context"])
        m["ctx_class"] = float(any(q["gold_chunk_ids"].get(d, 0) >= 2 for d in r["context"]))
        rows.append({"qid": r["qid"], "config": r["config"], "style": q["style"], "stratum": q["stratum"], **m})
        per[r["config"]].append({"style": q["style"], "stratum": q["stratum"], **m})

    def agg(items: list[dict]) -> dict:
        keys = [k for k in items[0] if k not in ("style", "stratum")]
        return {"n": len(items), **{k: round(sum(x[k] for x in items) / len(items), 4) for k in keys}}

    summary = {}
    for c, items in per.items():
        summary[c] = {
            "all": agg(items),
            "by_style": {
                s: agg([x for x in items if x["style"] == s]) for s in ("identifier", "descriptive") if any(x["style"] == s for x in items)
            },
            "by_stratum": {s: agg([x for x in items if x["stratum"] == s]) for s in sorted({x["stratum"] for x in items})},
        }
    out_dir = ROOT / "runs" / run_id
    (out_dir / "retrieval_metrics.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    (out_dir / "retrieval_metrics_per_question.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return summary


def table(
    summary: dict, cols=("strict@1", "strict@5", "class@1", "class@5", "class@10", "class@20", "soft@5", "mrr@10", "ndcg@10", "ctx_class")
) -> str:
    lines = ["| config | n | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    for c, s in summary.items():
        a = s["all"]
        lines.append(f"| {c} | {a['n']} | " + " | ".join(f"{a[k]:.3f}" for k in cols) + " |")
    return "\n".join(lines)
