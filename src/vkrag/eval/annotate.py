"""Manual annotation (PLAN §7.2 judge calibration, §9.3): blind CSV export, validated import, Cohen's kappa.

`export --task judge_calibration`: 80 answers stratified by answerer x configuration, balanced over
stratum and answer_type inside each cell (not by the judge label); split 40 tuning / 40 held-out by
code (seed) before the export. The CSV (UTF-8 with BOM for Excel) has opaque item ids, shuffled order
and only what the annotator must see: question, reference answer, the rule(s), the masked answer.
The key (`*.key.jsonl`: item -> qid, answerer, config, answer key, split) is not for the annotator.
`import` validates the label columns, merges with the key and reports kappa against the judge:
linear-weighted for correctness, plain for abstained / hallucination, with cluster-free bootstrap 95% CI.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from vkrag.config import ROOT, load_config

LABELS = {"correctness": ("correct", "partial", "incorrect"), "abstained": ("true", "false"),
          "hallucination": ("true", "false")}
N_ITEMS, N_TUNE = 80, 40


def _dir(run_id: str) -> Path:
    d = ROOT / "runs" / run_id / "annotations"
    d.mkdir(parents=True, exist_ok=True)
    return d


def select(answers: list[dict], qs: dict, seed: int, n: int = N_ITEMS) -> list[dict]:
    """Round-robin over (answerer, config) cells; inside a cell the answer whose (stratum, answer_type)
    is least represented so far."""
    rng = random.Random(seed)
    cells = defaultdict(list)
    for a in answers:
        cells[(a["answerer"], a["config"])].append(a)
    for v in cells.values():
        v.sort(key=lambda a: a["key"])
        rng.shuffle(v)
    order = sorted(cells)
    rng.shuffle(order)
    seen: Counter = Counter()
    out = []
    while len(out) < n and any(cells.values()):
        for cell in order:
            if len(out) == n or not cells[cell]:
                continue
            def k(a):
                q = qs[a["qid"]]
                return seen[(q["stratum"], q.get("answer_type"))], seen[a["qid"]]
            best = min(cells[cell], key=k)
            cells[cell].remove(best)
            q = qs[best["qid"]]
            seen[(q["stratum"], q.get("answer_type"))] += 1
            seen[best["qid"]] += 1
            out.append(best)
    return out


def export(sample: str, run_id: str, configs: tuple[str, ...]) -> dict:
    from vkrag.eval.judge import current_answers, vu_texts
    from vkrag.eval.masking import mask

    seed = load_config()["seed"]
    answers, qs = current_answers(sample, run_id)
    answers = [a for a in answers if a["config"] in configs and not a["missing"] and a["repeat_idx"] == 0]
    items = select(answers, qs, seed)
    rng = random.Random(seed + 1)
    by_answerer = defaultdict(list)
    for a in items:
        by_answerer[a["answerer"]].append(a)
    split = {}
    for v in by_answerer.values():  # tuning / held-out balanced by answerer
        rng.shuffle(v)
        for i, a in enumerate(v):
            split[a["key"]] = "tune" if i % 2 == 0 else "heldout"
    vtext = vu_texts()
    d = _dir(run_id)
    rows, keys = [], []
    for a in items:
        q = qs[a["qid"]]
        iid = "J" + hashlib.sha256(f"{seed}:{a['key']}".encode()).hexdigest()[:8]
        if q["stratum"] == "unanswerable":
            rules = "UNANSWERABLE (false premise). " + q.get("rationale", "") + "\n" + "\n".join(
                e["text"] for e in q.get("spec_evidence") or [])
        else:
            rules = "\n\n".join([vtext[q["vuid"]]] + [vtext[x] for x in q.get("acceptable_vuids") or [] if x in vtext])
        qtext = q["question"] + (f"\n[expected verdict: {q['expected_verdict']}]" if q.get("expected_verdict") else "")
        rows.append({"item_id": iid, "split": split[a["key"]], "question_type": q.get("answer_type") or "unanswerable",
                     "question": qtext, "reference_answer": q["reference_answer"], "rules": rules,
                     "answer": mask(a["answer"])[0]})
        keys.append({"item_id": iid, "qid": a["qid"], "answerer": a["answerer"], "config": a["config"],
                     "answer_key": a["key"], "split": split[a["key"]]})
    rng.shuffle(rows)
    header = list(rows[0]) + [f"{k}[{'|'.join(v)}]" for k, v in LABELS.items()] + ["comment"]
    for part in ("tune", "heldout"):
        with open(d / f"judge_calibration_{part}.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            for r in rows:
                if r["split"] == part:
                    w.writerow(list(r.values()) + [""] * (len(LABELS) + 1))
    with open(d / "judge_calibration.key.jsonl", "w", encoding="utf-8") as f:
        for k in keys:
            f.write(json.dumps(k) + "\n")
    c = Counter((k["answerer"], k["split"]) for k in keys)
    return {"items": len(rows), "by_answerer_split": {f"{a}/{s}": n for (a, s), n in sorted(c.items())},
            "configs": dict(Counter(k["config"] for k in keys)),
            "files": [str((d / f"judge_calibration_{p}.csv").relative_to(ROOT)) for p in ("tune", "heldout")]}


def import_labels(run_id: str, part: str) -> dict:
    d = _dir(run_id)
    keys = {k["item_id"]: k for k in map(json.loads, open(d / "judge_calibration.key.jsonl", encoding="utf-8"))}
    out, errors = [], []
    with open(d / f"judge_calibration_{part}.csv", encoding="utf-8-sig", newline="") as f:
        for n, r in enumerate(csv.DictReader(f), 2):
            lab = {}
            for k, allowed in LABELS.items():
                col = f"{k}[{'|'.join(allowed)}]"
                v = (r.get(col) or "").strip().lower()
                if v not in allowed:
                    errors.append(f"line {n}: {k}={v!r}")
                lab[k] = v == "true" if allowed == ("true", "false") else v
            if r["item_id"] not in keys:
                errors.append(f"line {n}: unknown item {r['item_id']}")
                continue
            out.append(keys[r["item_id"]] | {"human": lab, "comment": r.get("comment", "")})
    if errors:
        return {"errors": errors[:30], "n_errors": len(errors)}
    with open(d / f"judge_calibration_{part}.labels.jsonl", "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"labels": len(out)} | agreement(run_id, out)


def cohen_kappa(a: list, b: list, cats: list, weighted: bool = False) -> float | None:
    n, k = len(a), len(cats)
    if n == 0:
        return None
    idx = {c: i for i, c in enumerate(cats)}
    w = [[(abs(i - j) / (k - 1) if weighted else float(i != j)) for j in range(k)] for i in range(k)]
    obs = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[idx[x]][idx[y]] += 1 / n
    pa = [sum(obs[i]) for i in range(k)]
    pb = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    do = sum(w[i][j] * obs[i][j] for i in range(k) for j in range(k))
    de = sum(w[i][j] * pa[i] * pb[j] for i in range(k) for j in range(k))
    return None if de == 0 else 1 - do / de


def agreement(run_id: str, labels: list[dict], n_boot: int | None = None) -> dict:
    from vkrag.eval.judge import _jsonl, prompt

    cfg = load_config()
    n_boot = n_boot or cfg["eval"]["bootstrap"]
    ph = prompt("correctness")[1]
    judge = {r["answer_key"]: r["verdict"] for r in _jsonl(ROOT / "runs" / run_id / "judgments.jsonl")
             if r["kind"] == "correctness" and r["prompt_hash"] == ph and not r["failed"] and r["judge_repeat_idx"] == 0}
    pairs = [(l["human"], judge[l["answer_key"]]) for l in labels if l["answer_key"] in judge]
    rng = random.Random(cfg["seed"])
    out = {"paired": len(pairs)}
    specs = {"correctness": (list(LABELS["correctness"]), True), "abstained": ([True, False], False),
             "hallucination": ([True, False], False)}
    for field, (cats, weighted) in specs.items():
        a = [h[field] for h, _ in pairs]
        b = [j[field] for _, j in pairs]
        kap = cohen_kappa(a, b, cats, weighted)
        boots = []
        for _ in range(n_boot):
            ix = [rng.randrange(len(pairs)) for _ in pairs]
            v = cohen_kappa([a[i] for i in ix], [b[i] for i in ix], cats, weighted)
            if v is not None:
                boots.append(v)
        boots.sort()
        ci = (round(boots[int(0.025 * len(boots))], 3), round(boots[int(0.975 * len(boots)) - 1], 3)) if boots else None
        out[field] = {"kappa": None if kap is None else round(kap, 3), "ci95": ci,
                      "agreement": round(sum(x == y for x, y in zip(a, b)) / len(a), 3) if a else None}
    return out
