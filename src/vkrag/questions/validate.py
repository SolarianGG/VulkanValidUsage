"""Stage 3a: automatic checks of the generator output (PLAN §4 Stage 3 "Automatic filters", §9.3).

`validate(sample)` reads every batch_NNN.output.jsonl (and batch_unans.output.jsonl) of the sample,
checks each line and writes:
  batches/<sample>/batch_NNN.rejects.jsonl    rejected lines with reasons
  generation_log/<sample>_validated.jsonl     accepted lines + question_hash + derived fields
  generation_log/<sample>_validation.json     counts, reasons, per-batch drift statistics
A VU whose identifier or descriptive line is rejected is reported in `regenerate`.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from statistics import mean

from vkrag.config import EXTERNAL, PROCESSED, load_config
from vkrag.index.tokenize import TOKEN, is_identifier, leak_ngrams
from vkrag.questions.prepare import ANSWER_TYPES, GLOG, STYLES

UNANS_SUBTYPES = ("nonexistent", "false_rule", "false_behavior")
VUID_RE = re.compile(r"VUID")
FIVE_DIGITS = re.compile(r"\b\d{5}\b")
# unit symbols with an inner capital that are not API identifiers
UNITS = frozenset({"KiB", "MiB", "GiB", "TiB", "KB", "MB", "GB", "kB", "ns", "ms", "Hz", "kHz", "MHz", "GHz"})
VK_PREFIX = re.compile(r"^(vk|Vk|VK_)")
EXTENSION_RE = re.compile(r"\b(VK|SPV|GL|GLSL)_[A-Z0-9]+_\w+")
SENTENCE_START = re.compile(r"(^|[.!?:;]\s+|\(\s*|\"\s*)$")


def question_hash(q: str) -> str:
    return hashlib.sha256(q.strip().encode("utf-8")).hexdigest()[:16]


class Lexicon:
    def __init__(self) -> None:
        ids = json.load(open(PROCESSED / "identifiers.json", encoding="utf-8"))
        names: set[str] = set()
        for v in ids["by_kind"].values():
            names.update(v)
        names.update(ids.get("outdated", []))
        names.update(ids.get("newer", []))
        al = json.load(open(PROCESSED / "aliases.json", encoding="utf-8"))
        names.update(al["alias_to_target"])
        names.update(al["alias_to_target"].values())
        self.vk = names
        self.spirv = {l.strip() for l in open(EXTERNAL / "spirv_identifiers.txt", encoding="utf-8") if l.strip()}

    def exists(self, name: str) -> bool:
        return name in self.vk or name in self.spirv


def identifiers_in(text: str, lex: Lexicon) -> list[str]:
    """Identifiers in the sense of PLAN §4 Stage 3: vk/Vk/VK_ prefix, multi-word camelCase or SNAKE_CASE,
    or a SPIR-V/GLSL dictionary word. A capitalized dictionary word at the start of a sentence is
    not counted (e.g. "Input" opening a sentence)."""
    found: list[str] = []
    for m in TOKEN.finditer(text):
        t = m.group(0)
        if t[0].isdigit() or t in UNITS:
            continue
        if VK_PREFIX.match(t) and len(t) > 2 or is_identifier(t):
            found.append(t)
        elif t in lex.spirv and not t.islower():
            if t[0].isupper() and t[1:].islower() and SENTENCE_START.search(text[: m.start()]):
                continue
            found.append(t)
    return found


def _load_jsonl(path) -> list[dict]:
    out = []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as e:
            out.append({"_parse_error": f"line {n}: {e}"})
    return out


def check_answerable(rec: dict, item: dict, ctx_vus: dict[str, set[str]], lex: Lexicon, ngram_max: int) -> list[str]:
    r: list[str] = []
    style = rec.get("style")
    if style not in STYLES:
        r.append(f"bad style {style!r}")
    if rec.get("answer_type") not in ANSWER_TYPES:
        r.append(f"bad answer_type {rec.get('answer_type')!r}")
    if rec.get("answer_type") != item["answer_type"] and not (rec.get("answer_type") == "rule" and rec.get("downgraded_to_rule")):
        r.append("answer_type differs from the assigned one without downgraded_to_rule")
    if style == "descriptive" and rec.get("descriptive_infeasible"):
        return r  # question and reference intentionally null
    if rec.get("answer_type") == "yes_no":
        ev = rec.get("expected_verdict")
        if ev not in ("yes", "no"):
            r.append("yes_no without expected_verdict")
        elif ev != item.get("expected_verdict") and not rec.get("verdict_changed"):
            r.append("expected_verdict differs from the assigned one without verdict_changed")
        ra = (rec.get("reference_answer") or "").lstrip().lower()
        if ev in ("yes", "no") and not ra.startswith(ev):
            r.append("reference_answer does not start with the verdict")
    q = rec.get("question")
    if not isinstance(q, str) or not q.strip():
        return r + ["empty question"]
    if not isinstance(rec.get("reference_answer"), str) or not rec["reference_answer"].strip():
        r.append("empty reference_answer")
    entity_suffixes = {v.rsplit("-", 1)[-1] for v in ctx_vus.get(item["entity"], set())}
    if VUID_RE.search(q) or any(n in entity_suffixes for n in FIVE_DIGITS.findall(q)):
        r.append("question mentions a VUID or a VU number")
    n_content, n_stop = leak_ngrams(q, item["vu_text"])
    if max(n_content, n_stop) > ngram_max:
        r.append(f"common n-gram with the VU text = {n_content} (content) / {n_stop} (with stop words) > {ngram_max}")
    if style == "descriptive":
        ids = identifiers_in(q, lex)
        if ids or EXTENSION_RE.search(q):
            r.append(f"identifiers in a descriptive question: {sorted(set(ids))}")
    covered: set[str] = set()
    for e in rec.get("checked_entities") or []:
        covered |= ctx_vus.get(e, set())
    covered |= set(rec.get("checked_vuids") or [])
    missing = ctx_vus.get(item["entity"], set()) - covered
    if missing:
        r.append(f"checked_* miss {len(missing)} VUs of the target entity")
    if rec.get("answer_type") == "scenario":
        miss_rel = [e for e in item["related_entities"] if not ctx_vus.get(e, set()) <= covered]
        if miss_rel:
            r.append(f"scenario: related entities not checked: {miss_rel}")
    if rec.get("also_relevant_vuids"):
        r.append(f"also_relevant_vuids not empty: {rec['also_relevant_vuids']}")
    return r


def check_pair(recs: dict[str, dict]) -> list[str]:
    a, b = recs.get("identifier"), recs.get("descriptive")
    if not a or not b:
        return [f"missing style line(s): {sorted(set(STYLES) - set(recs))}"]
    r = []
    if a.get("answer_type") != b.get("answer_type"):
        r.append("answer_type differs between styles")
    if a.get("expected_verdict") != b.get("expected_verdict") and not b.get("descriptive_infeasible"):
        r.append("expected_verdict differs between styles")
    return r


def check_unanswerable(rec: dict, lex: Lexicon) -> list[str]:
    r = []
    st = rec.get("subtype")
    if st not in UNANS_SUBTYPES:
        r.append(f"bad subtype {st!r}")
    for k in ("question", "reference_answer", "rationale"):
        if not isinstance(rec.get(k), str) or not rec[k].strip():
            r.append(f"empty {k}")
    if st == "nonexistent":
        inv = rec.get("invented_identifiers") or []
        if not inv:
            r.append("nonexistent without invented_identifiers")
        for name in inv:
            if lex.exists(name):
                r.append(f"invented identifier exists: {name}")
            if name not in (rec.get("question") or ""):
                r.append(f"invented identifier not in the question: {name}")
    elif st in ("false_rule", "false_behavior") and not rec.get("spec_evidence"):
        r.append("false premise without spec_evidence")
    if VUID_RE.search(rec.get("question") or ""):
        r.append("question mentions a VUID or a VU number")
    return r


def drift(recs: list[dict]) -> dict:
    qs = [x for x in recs if isinstance(x.get("question"), str)]
    return {
        "lines": len(recs),
        "mean_words": round(mean(len(x["question"].split()) for x in qs), 1) if qs else None,
        "answer_type": dict(Counter(x.get("answer_type") for x in recs)),
        "downgraded": sum(bool(x.get("downgraded_to_rule")) for x in recs),
        "verdict_changed": sum(bool(x.get("verdict_changed")) for x in recs),
        "descriptive_infeasible": sum(bool(x.get("descriptive_infeasible")) for x in recs if x.get("style") == "descriptive"),
    }


def validate(sample: str, dedup: bool = False) -> dict:
    cfg = load_config()
    ngram_max = cfg["questions"]["ngram_max"]
    lex = Lexicon()
    bdir = GLOG / "batches" / sample
    accepted: list[dict] = []
    reasons: Counter = Counter()
    per_batch: dict[str, dict] = {}
    regenerate: list[str] = []
    missing_outputs: list[str] = []
    superseded: list[str] = []
    inputs = {p: json.load(open(p, encoding="utf-8")) for p in sorted(bdir.glob("batch_[0-9][0-9][0-9].input.json"))}
    latest = {i["vuid"]: inp["batch"] for inp in inputs.values() for i in inp["items"]}  # sorted -> last wins
    for inp_path, inp in inputs.items():
        out_path = inp_path.with_name(inp_path.name.replace(".input.json", ".output.jsonl"))
        if not out_path.exists():
            missing_outputs.append(out_path.name)
            continue
        items = {i["vuid"]: i for i in inp["items"] if latest[i["vuid"]] == inp["batch"]}
        superseded += [f"{i['vuid']}@{inp['batch']}" for i in inp["items"] if latest[i["vuid"]] != inp["batch"]]
        qid_to = {q: (i["vuid"], s) for i in inp["items"] for s, q in i["qids"].items()}
        ctx_vus = {e: {v["vuid"] for v in b["vus"]} for e, b in inp["context"]["entities"].items()}
        recs = _load_jsonl(out_path)
        rejects, by_vu = [], defaultdict(dict)
        for rec in recs:
            if "_parse_error" in rec:
                rejects.append({**rec, "reasons": ["json parse error"]})
                continue
            key = qid_to.get(rec.get("qid"))
            if not key or key != (rec.get("vuid"), rec.get("style")):
                rejects.append({**rec, "reasons": ["qid does not match the batch (vuid, style)"]})
                continue
            if rec["style"] in by_vu[rec["vuid"]]:
                rejects.append({**rec, "reasons": ["duplicate line for (vuid, style)"]})
                continue
            by_vu[rec["vuid"]][rec["style"]] = rec
        for vuid, item in items.items():
            pair = by_vu.get(vuid, {})
            pair_r = check_pair(pair)
            ok_all = True
            for style in STYLES:
                rec = pair.get(style)
                if rec is None:
                    ok_all = False
                    continue
                rs = check_answerable(rec, item, ctx_vus, lex, ngram_max) + pair_r
                if rs:
                    ok_all = False
                    rejects.append({**rec, "reasons": rs})
                    reasons.update(x.split(":")[0].split(" =")[0] for x in rs)
                else:
                    accepted.append({**rec, "stratum": item["stratum"], "entity": item["entity"], "entity_kind": item["entity_kind"],
                                     "equiv_class_id": None, "batch": inp["batch"],
                                     "question_hash": question_hash(rec["question"]) if rec.get("question") else None})
            if not ok_all:
                regenerate.append(vuid)
        rej_path = inp_path.with_name(inp_path.name.replace(".input.json", ".rejects.jsonl"))
        rej_path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rejects), encoding="utf-8")
        per_batch[inp_path.name] = {**drift(recs), "rejected": len(rejects)}

    # unanswerable
    un_in = bdir / "batch_unans.input.json"
    un_out = bdir / "batch_unans.output.jsonl"
    unans = {"present": un_out.exists()}
    if un_out.exists():
        uin = json.load(open(un_in, encoding="utf-8"))
        recs = _load_jsonl(un_out)
        rejects, ok = [], []
        for rec in recs:
            rs = ["json parse error"] if "_parse_error" in rec else check_unanswerable(rec, lex)
            if not str(rec.get("qid", "")).startswith(uin["qid_prefix"]):
                rs.append("qid without the batch prefix")
            (rejects if rs else ok).append({**rec, "reasons": rs} if rs else rec)
        for rec in ok:
            accepted.append({**rec, "stratum": "unanswerable", "question_hash": question_hash(rec["question"])})
        (bdir / "batch_unans.rejects.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rejects), encoding="utf-8")
        have = Counter(r["subtype"] for r in ok)
        unans.update({"accepted": dict(have), "rejected": len(rejects),
                      "quota_short": {k: v - have.get(k, 0) for k, v in uin["quotas"].items() if have.get(k, 0) < v}})

    # equivalence class of the gold VU (for gold_chunk_ids at freeze)
    eq = {}
    for line in open(PROCESSED / "strata.jsonl", encoding="utf-8"):
        s = json.loads(line)
        eq[s["vuid"]] = s["equiv_class_id"]
    for a in accepted:
        if a.get("vuid"):
            a["equiv_class_id"] = eq.get(a["vuid"])

    dups = None
    if dedup:
        from vkrag.questions.dedup import near_duplicates

        dups = near_duplicates(accepted, cfg["questions"]["dup_cosine"])

    (GLOG / f"{sample}_validated.jsonl").write_text("".join(json.dumps(a, ensure_ascii=False) + "\n" for a in accepted), encoding="utf-8")
    report = {
        "sample": sample,
        "missing_outputs": missing_outputs,
        "accepted_lines": len(accepted),
        "reject_reasons": dict(reasons.most_common()),
        "regenerate_vuids": sorted(set(regenerate)),
        "superseded": superseded,
        "per_batch": per_batch,
        "unanswerable": unans,
        "near_duplicates": dups,
    }
    (GLOG / f"{sample}_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report
