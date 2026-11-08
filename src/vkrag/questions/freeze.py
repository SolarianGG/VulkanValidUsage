"""Stage 3a freeze: the immutable question set of a sample (PLAN §4 Stage 3, §7.1, §9.2 item 3).

Writes data/questions/<sample>_questions.jsonl (main: questions.jsonl) and <name>.manifest.json.
Each answerable question gets graded gold chunks (PLAN §7.1):
  3  the gold VU chunk of the target VU
  2  VU chunks of the same equivalence class (and, after Stage 3b, of acceptable_vuids classes)
  1  parts of the parent section and sections linked from the VU `refs`
`in_generation` marks the one style per VU that goes to the expensive phases (gen_style; identifier
when the descriptive question is infeasible). Unanswerable questions have no gold and are always
in generation. `gold_final` stays false until Stage 3b adds acceptable_vuids.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict

from vkrag.config import DATA, PROCESSED
from vkrag.questions.prepare import GLOG
from vkrag.questions.validate import question_hash


def out_path(sample: str):
    return DATA / "questions" / ("questions.jsonl" if sample == "main" else f"{sample}_questions.jsonl")


def gold_chunks(vuid: str, vu: dict, by_class: dict, sections: dict, anchor: dict, chunk_section: dict) -> dict[str, int]:
    rel: dict[str, int] = {}

    def put(cid: str, g: int) -> None:
        rel[cid] = max(rel.get(cid, 0), g)

    for cid in sections.get(vu["section_id"], []):
        put(cid, 1)
    for r in vu.get("refs", []):
        cid = anchor.get(r)
        if cid and cid in chunk_section:  # section chunks only; VU anchors are handled by the class
            put(cid, 1)
    for other in by_class[vu["equiv_class_id"]]:
        put(other, 2)
    put(vuid, 3)
    return dict(sorted(rel.items(), key=lambda kv: (-kv[1], kv[0])))


def freeze(sample: str, force: bool = False) -> dict:
    path = out_path(sample)
    if path.exists() and not force:
        raise FileExistsError(f"{path} exists; the question set is immutable (use --force only before approval)")
    report = json.load(open(GLOG / f"{sample}_validation.json", encoding="utf-8"))
    if report["missing_outputs"] or report["regenerate_vuids"]:
        raise RuntimeError(f"validation not clean: missing {report['missing_outputs']}, regenerate {report['regenerate_vuids']}")
    asg = json.load(open(GLOG / f"{sample}_assignments.json", encoding="utf-8"))["assignments"]
    recs = [json.loads(l) for l in open(GLOG / f"{sample}_validated.jsonl", encoding="utf-8")]

    vus = {}
    by_class: dict[str, list[str]] = defaultdict(list)
    for line in open(PROCESSED / "vuids.jsonl", encoding="utf-8"):
        v = json.loads(line)
        vus[v["vuid"]] = v
        by_class[v["equiv_class_id"]].append(v["vuid"])
    sections: dict[str, list[str]] = defaultdict(list)
    chunk_section: dict[str, str] = {}
    for line in open(PROCESSED / "chunks.jsonl", encoding="utf-8"):
        c = json.loads(line)
        if c["type"] == "section":
            sections[c["section_id"]].append(c["chunk_id"])
            chunk_section[c["chunk_id"]] = c["section_id"]
    anchor = json.load(open(PROCESSED / "anchor_map.json", encoding="utf-8"))
    corpus_hash = json.load(open(PROCESSED / "coverage_report.json", encoding="utf-8")).get("corpus_hash")

    infeasible = {r["vuid"] for r in recs if r.get("style") == "descriptive" and r.get("descriptive_infeasible")}
    out = []
    for r in recs:
        if r.get("stratum") == "unanswerable":
            out.append({"qid": r["qid"], "sample": sample, "stratum": "unanswerable", "subtype": r["subtype"],
                        "style": r.get("style", "identifier"), "question": r["question"],
                        "reference_answer": r["reference_answer"], "rationale": r["rationale"],
                        "spec_evidence": r.get("spec_evidence") or [], "invented_identifiers": r.get("invented_identifiers") or [],
                        "in_generation": True, "question_hash": question_hash(r["question"])})
            continue
        if not r.get("question"):
            continue  # descriptive_infeasible placeholder
        v = r["vuid"]
        a = asg[v]
        gen_style = "identifier" if v in infeasible else a["gen_style"]
        q = {
            "qid": r["qid"], "sample": sample, "vuid": v, "entity": r["entity"], "entity_kind": r["entity_kind"],
            "stratum": r["stratum"], "equiv_class_id": vus[v]["equiv_class_id"], "style": r["style"],
            "answer_type": r["answer_type"], "assigned_answer_type": a["answer_type"],
            "expected_verdict": r.get("expected_verdict") if r["answer_type"] == "yes_no" else None,
            "question": r["question"], "reference_answer": r["reference_answer"],
            "descriptive_infeasible": v in infeasible, "paired_qid": a["qids"]["descriptive" if r["style"] == "identifier" else "identifier"],
            "in_generation": r["style"] == gen_style, "batch": r["batch"],
            "gold_chunk_ids": gold_chunks(v, vus[v], by_class, sections, anchor, chunk_section),
            "acceptable_vuids": [], "gold_final": False,
            "question_hash": question_hash(r["question"]),
        }
        out.append(q)
    out.sort(key=lambda q: (q["stratum"] == "unanswerable", q["qid"]))
    text = "".join(json.dumps(q, ensure_ascii=False) + "\n" for q in out)
    path.write_text(text, encoding="utf-8")
    ans = [q for q in out if q["stratum"] != "unanswerable"]
    manifest = {
        "sample": sample, "file": path.name, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "questions": len(out), "answerable": len(ans), "unanswerable": len(out) - len(ans),
        "in_generation": sum(q["in_generation"] for q in out), "corpus_hash": corpus_hash,
        "gold_final": False, "stage": "3a",
        "gold_class_size": {"max": max(len(by_class[q["equiv_class_id"]]) for q in ans),
                            "multi": sum(len(by_class[q["equiv_class_id"]]) > 1 for q in ans)},
    }
    path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest
