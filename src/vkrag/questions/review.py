"""Pilot review sheet (checkpoint PLAN §5.2) and the n-gram filter strictness comparison.

`review(sample)` reads <sample>_validated.jsonl and writes reports/<sample>_questions.md:
per VU the target rule, both styles with their reference answers, and three leak measures:
  ngram_content   the filter in use: unstemmed words without stop words and identifiers
  ngram_stop      the same with stop words kept (the stricter variant under evaluation)
  fuzz            rapidfuzz partial_ratio between question and VU text (character level)
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

from rapidfuzz import fuzz

from vkrag.config import ROOT
from vkrag.index.tokenize import leak_ngrams
from vkrag.questions.prepare import GLOG


def leak_measures(question: str, vu_text: str) -> dict:
    n_content, n_stop = leak_ngrams(question, vu_text)
    return {"ngram_content": n_content, "ngram_stop": n_stop,
            "fuzz": round(fuzz.partial_ratio(question.lower(), vu_text.lower()), 1)}


def review(sample: str) -> dict:
    recs = [json.loads(l) for l in open(GLOG / f"{sample}_validated.jsonl", encoding="utf-8")]
    items = {}
    for p in sorted((GLOG / "batches" / sample).glob("batch_[0-9][0-9][0-9].input.json")):
        for i in json.load(open(p, encoding="utf-8"))["items"]:
            items[i["vuid"]] = i
    by_vu: dict[str, list[dict]] = defaultdict(list)
    unans = []
    for r in recs:
        (unans.append(r) if r.get("stratum") == "unanswerable" else by_vu[r["vuid"]].append(r))
    lines = [f"# Pilot questions for review ({sample})", "",
             "Leak measures per question: `ngram_content` / `ngram_stop` (without / with stop words, both limited to 5), "
             "`fuzz` (character partial ratio, 0-100).", ""]
    rows = []
    for vuid in sorted(by_vu, key=lambda v: (items[v]["stratum"], v)):
        it = items[vuid]
        lines += [f"## {vuid}", f"- stratum `{it['stratum']}`, entity `{it['entity']}` ({it['entity_kind']}), "
                  f"assigned `{it['answer_type']}`" + (f", verdict `{it['expected_verdict']}`" if it.get("expected_verdict") else ""),
                  f"- **VU:** {it['vu_text']}", ""]
        for r in sorted(by_vu[vuid], key=lambda r: r["style"]):
            if not r.get("question"):
                lines += [f"**{r['style']}**: descriptive_infeasible", ""]
                continue
            m = leak_measures(r["question"], it["vu_text"])
            rows.append({"qid": r["qid"], "vuid": vuid, "style": r["style"], **m})
            flags = [k for k in ("downgraded_to_rule", "verdict_changed") if r.get(k)]
            lines += [f"**{r['style']}** `{r['qid']}` ({r['answer_type']}{', ' + ', '.join(flags) if flags else ''}; "
                      f"ngram {m['ngram_content']}/{m['ngram_stop']}, fuzz {m['fuzz']})",
                      f"- Q: {r['question']}", f"- A: {r['reference_answer']}"]
            if r.get("notes"):
                lines.append(f"- notes: {r['notes']}")
            lines.append("")
    if unans:
        lines += ["## Unanswerable", ""]
        for r in unans:
            lines += [f"**{r['subtype']}** `{r['qid']}`", f"- Q: {r['question']}", f"- A: {r['reference_answer']}",
                      f"- rationale: {r['rationale']}"]
            for ev in r.get("spec_evidence") or []:
                lines.append(f"- evidence ({ev.get('source')}): {ev.get('text')}")
            if r.get("invented_identifiers"):
                lines.append(f"- invented: {', '.join(r['invented_identifiers'])}")
            lines.append("")
    out = ROOT / "reports" / f"{sample}_questions.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rows.sort(key=lambda x: (-x["ngram_stop"], -x["fuzz"]))
    return {"path": str(out.relative_to(ROOT)), "questions": len(rows), "unanswerable": len(unans),
            "most_leaky": rows[:12],
            "ngram_stop_hist": dict(sorted(Counter(r["ngram_stop"] for r in rows).items()))}
