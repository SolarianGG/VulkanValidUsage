"""Stage 8 report artifacts (PLAN §4 Stage 8, as amended in §10 on 2026-11-10).

`vkrag report --run-id pilot` reads only frozen run outputs and writes:
- `reports/report_data.json`: every number the report quotes (tables 0-4, strata, calibration, length bias);
- `reports/report_tables.md`: the tables rendered as Markdown (pasted into `reports/report.md`);
- `reports/figures/*.png`: strata, Recall@k curves, Pareto score vs cost, score vs latency;
- `reports/error_candidates.md`: automatically selected error cases per category for the manual analysis.

Confidence intervals: cluster bootstrap by entity (unanswerable questions: one cluster per question),
the same scheme as `eval/hypotheses.py`. Nothing here calls a model or a paid API.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from vkrag.config import ROOT, load_config

GEN_CONFIGS = ("closed", "bm25", "dense", "rrf", "rrf_rerank", "rewrite_rrf_rerank", "hyde_rrf_rerank",
               "oracle", "oracle_distract", "rrf_rerank_strict", "rrf_rerank_k3", "rrf_rerank_k10")
RET_CONFIGS = ("bm25", "dense", "sparse", "rrf", "rrf_sparse", "bm25_rerank", "dense_rerank", "rrf_rerank",
               "rewrite_rrf", "rewrite_rrf_rerank", "rewrite_append_rrf_rerank", "hyde_rrf", "hyde_rrf_rerank",
               "oracle", "oracle_distract")
STRATA = ("recent", "ext_niche", "ext_popular", "core_promoted", "core_1_0")
ANSWERERS = ("qwen", "remote")
# reference categorical palette (dataviz skill), validated for the light surface: slots 1-4
COLORS = {"closed": "#eb6834", "rrf_rerank": "#2a78d6", "oracle": "#1baf7a", "extra": "#eda100"}
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#1f1f1e", "#6b6a66", "#e4e3df"


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(line) for line in open(p, encoding="utf-8") if line.strip()]


def _r(x, nd=3):
    return None if x is None else round(float(x), nd)


# ---------------------------------------------------------------- statistics

def cluster_mean_ci(rows: list[tuple[str, float]], n_boot: int, rng) -> dict:
    """Mean of values with a cluster bootstrap 95% CI; rows = (cluster, value)."""
    by = defaultdict(list)
    for c, v in rows:
        by[c].append(v)
    if not by:
        return {"mean": None, "ci95": None, "n": 0}
    s = np.array([sum(v) for v in by.values()], dtype=float)
    n = np.array([len(v) for v in by.values()], dtype=float)
    idx = rng.integers(len(s), size=(n_boot, len(s)))
    boots = s[idx].sum(axis=1) / n[idx].sum(axis=1)
    return {"mean": _r(s.sum() / n.sum()), "ci95": [_r(np.quantile(boots, 0.025)), _r(np.quantile(boots, 0.975))],
            "n": int(n.sum()), "clusters": len(s)}


def _fmt_ci(d: dict | None, pct: bool = False) -> str:
    if not d or d.get("mean") is None:
        return "-"
    m, (lo, hi) = d["mean"], d["ci95"]
    if pct:
        return f"{m * 100:.0f} [{lo * 100:.0f}, {hi * 100:.0f}]"
    return f"{m:.2f} [{lo:.2f}, {hi:.2f}]"


def _f(x, nd=2, pct=False) -> str:
    if x is None:
        return "-"
    return f"{x * 100:.0f}" if pct else f"{x:.{nd}f}"


# ---------------------------------------------------------------- loading

class Run:
    def __init__(self, run_id: str, sample: str):
        self.run_id, self.sample = run_id, sample
        self.dir = ROOT / "runs" / run_id
        self.cfg = load_config()
        self.rng = np.random.default_rng(self.cfg["seed"])
        self.n_boot = self.cfg["eval"]["bootstrap"]
        self.questions = _jsonl(ROOT / "data" / "questions" / f"{sample}_questions.jsonl")
        self.q = {x["qid"]: x for x in self.questions}
        self.scores = [r for r in _jsonl(self.dir / "scores.jsonl") if r["repeat_idx"] == 0]
        self.judgments = _jsonl(self.dir / "judgments.jsonl")
        self.gen = json.loads((self.dir / "generation_metrics.json").read_text(encoding="utf-8"))
        self.ret = json.loads((self.dir / "retrieval_metrics.json").read_text(encoding="utf-8"))
        self.ret_q = _jsonl(self.dir / "retrieval_metrics_per_question.jsonl")
        self.hyp = json.loads((self.dir / "hypotheses.json").read_text(encoding="utf-8"))

    def cluster(self, qid: str) -> str:
        return self.q[qid].get("entity") or qid

    def cell(self, answerer: str, config: str, answerable: bool = True) -> list[dict]:
        return [r for r in self.scores if r["answerer"] == answerer and r["config"] == config
                and r["answerable"] == answerable]

    def ci(self, rows: list[dict], f) -> dict:
        return cluster_mean_ci([(self.cluster(r["qid"]), float(f(r))) for r in rows], self.n_boot, self.rng)


# ---------------------------------------------------------------- table 0: corpus and sample

def table0(run: Run) -> dict:
    cov = json.loads((ROOT / "data" / "processed" / "coverage_report.json").read_text(encoding="utf-8"))
    strata_counts = Counter()
    for line in open(ROOT / "data" / "processed" / "strata.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if not r.get("excluded"):
            strata_counts[r["stratum"]] += 1
    ans = [x for x in run.questions if x["stratum"] != "unanswerable"]
    gold_class = Counter(sum(1 for g in x["gold_chunk_ids"].values() if g >= 2) for x in ans)
    sel = Counter(x["stratum"] for x in ans if x["style"] == "identifier")
    return {
        "spec_tag": run.cfg.get("spec", {}).get("tag"),
        "vu_total": cov["headers_diff"]["headers_total"],
        "explicit_total": cov["explicit_total"], "coverage": cov["coverage"],
        "headers_only_in_build": len(cov["headers_diff"]["only_in_build"]),
        "headers_only_in_headers": len(cov["headers_diff"]["only_in_headers"]),
        "chunks_by_type": cov["chunks_by_type"], "chunk_tokens": cov["length_tokens_max_of_three"],
        "equivalence": {"explicit_classes": cov["equivalence"]["explicit_classes"],
                        "size_distribution": cov["equivalence"]["size_distribution"]},
        "strata_available": dict(strata_counts), "strata_selected_vus": dict(sel),
        "questions": {"total": len(run.questions), "answerable": len(ans),
                      "unanswerable": len(run.questions) - len(ans),
                      "in_generation": sum(x["in_generation"] for x in run.questions),
                      "style": dict(Counter(x["style"] for x in ans)),
                      "answer_type": dict(Counter(x["answer_type"] for x in ans)),
                      "descriptive_infeasible": sum(x["descriptive_infeasible"] for x in ans),
                      "with_acceptable_vuids": sum(bool(x["acceptable_vuids"]) for x in ans),
                      "gold_class_size": {str(k): v for k, v in sorted(gold_class.items())}},
    }


# ---------------------------------------------------------------- table 1: retrieval

def _chunk_types(ids: set[str]) -> dict[str, str]:
    out = {}
    for line in open(ROOT / "data" / "processed" / "chunks.jsonl", encoding="utf-8"):
        if not line.startswith('{"chunk_id": "sec-'):
            continue
        r = json.loads(line)
        if r["chunk_id"] in ids:
            out[r["chunk_id"]] = r["section_kind"]
    return out


def table1(run: Run) -> dict:
    retrieved = _jsonl(run.dir / "retrieved.jsonl")
    sec = {c for r in retrieved for c in r["context"] if c.startswith("sec-")}
    kinds = _chunk_types(sec)
    ctx_types: dict[str, Counter] = defaultdict(Counter)
    ans = {x["qid"] for x in run.questions if x["stratum"] != "unanswerable"}
    for r in retrieved:
        if r["qid"] in ans:
            for c in r["context"]:
                ctx_types[r["config"]]["vu" if c.startswith("VUID-") else kinds.get(c, "section")] += 1
    per_q = defaultdict(list)
    for r in run.ret_q:
        per_q[r["config"]].append(r)
    out = {}
    for c in RET_CONFIGS:
        if c not in run.ret:
            continue
        m = run.ret[c]
        tot = sum(ctx_types[c].values()) or 1
        out[c] = {"all": m["all"], "by_style": m["by_style"], "by_stratum": m["by_stratum"],
                  "class@5_ci": run.ci(per_q[c], lambda r: r["class@5"]),
                  "ctx_types": {k: _r(v / tot) for k, v in ctx_types[c].items()}}
    return out


# ---------------------------------------------------------------- table 2: generation

def _faith(run: Run) -> dict[tuple[str, str], dict]:
    """Faithfulness verdict shares per (answerer, config), answerable questions, latest judge call."""
    from vkrag.eval.judge import prompt

    ph = prompt("faithfulness")[1]
    ansq = {x["qid"] for x in run.questions if x["stratum"] != "unanswerable"}
    latest = {}
    for j in run.judgments:
        if j["kind"] == "faithfulness" and j["prompt_hash"] == ph and not j["failed"] and j["qid"] in ansq:
            latest[(j["qid"], j["answerer"], j["config"])] = j["verdict"]
    out = defaultdict(Counter)
    for (_, a, c), v in latest.items():
        out[(a, c)][v["faithfulness"]] += 1
    return {k: {f: _r(n / sum(v.values())) for f, n in v.items()} for k, v in out.items()}


def table2(run: Run) -> dict:
    faith = _faith(run)
    out = {}
    for a in ANSWERERS:
        for c in GEN_CONFIGS:
            rows = run.cell(a, c)
            if not rows:
                continue
            g = run.gen[f"{a}|{c}|answerable"]
            out[f"{a}|{c}"] = g | {
                "score_ci": run.ci(rows, lambda r: r["score"]),
                "correct_ci": run.ci(rows, lambda r: r["score"] == 1.0),
                "hallucination_ci": run.ci(rows, lambda r: bool(r["hallucination"])),
                "faithfulness": faith.get((a, c)),
                "latency_s_p95": _r(np.quantile([r["latency_s"] for r in rows if r["latency_s"] is not None], 0.95), 2),
                "reasoning_tokens_mean": _r(np.mean([r["reasoning_tokens"] or 0 for r in rows]), 1),
            }
    return out


def unanswerable(run: Run) -> dict:
    out = {}
    for a in ANSWERERS:
        for c in GEN_CONFIGS:
            rows = run.cell(a, c, answerable=False)
            if not rows:
                continue
            out[f"{a}|{c}"] = {"n": len(rows),
                               "rejected_premise": sum(r["correctness"] == "correct" for r in rows),
                               "accepted_premise": sum(r["correctness"] == "incorrect" and bool(r["hallucination"])
                                                       for r in rows),
                               "partial": sum(r["correctness"] == "partial" for r in rows),
                               "abstained": sum(bool(r["abstained"]) for r in rows)}
    return out


def by_stratum(run: Run) -> dict:
    out = {}
    for a in ANSWERERS:
        for c in ("closed", "rrf_rerank", "oracle"):
            rows = run.cell(a, c)
            out[f"{a}|{c}"] = {s: run.ci([r for r in rows if r["stratum"] == s], lambda r: r["score"]) for s in STRATA}
    return out


def by_gold_in_context(run: Run) -> dict:
    """Score split by whether the gold class reached the assembled context (`ctx_class`)."""
    rq = {(r["qid"], r["config"]): r for r in run.ret_q}
    out = {}
    for c in ("bm25", "dense", "rrf", "rrf_rerank", "rewrite_rrf_rerank", "hyde_rrf_rerank"):
        for a in ANSWERERS:
            g = defaultdict(list)
            for r in run.cell(a, c):
                g["in" if rq[(r["qid"], c)]["ctx_class"] else "out"].append(r)
            out[f"{a}|{c}"] = {k: run.ci(v, lambda r: r["score"]) for k, v in g.items()}
    return out


def bare_verdicts(run: Run) -> dict:
    """Sensitivity: answers that are only "Yes." / "No." with the expected verdict. The judge scores them
    `partial` (no justification); none of them was in the 80 calibration items. Rescored as correct here."""
    answers = {(a["qid"], a["answerer"], a["config"]): (a["answer"] or "").strip()
               for a in _jsonl(run.dir / "answers.jsonl") if a["repeat_idx"] == 0}
    out = {}
    n_bare = 0
    for a in ANSWERERS:
        for c in GEN_CONFIGS:
            rows = run.cell(a, c)
            if not rows:
                continue
            adj = []
            for r in rows:
                txt = answers.get((r["qid"], a, c), "").lower().rstrip(".")
                exp = run.q[r["qid"]].get("expected_verdict")
                bare = not r["missing"] and txt in ("yes", "no") and txt == exp and r["correctness"] == "partial"
                n_bare += bare
                adj.append(1.0 if bare else float(r["score"]))
            out[f"{a}|{c}"] = {"score": _r(np.mean([r["score"] for r in rows])), "score_bare_as_correct": _r(np.mean(adj))}
    return {"rescored_answers": n_bare, "cells": out}


def yes_no_baseline(run: Run) -> dict:
    yn = [x for x in run.questions if x.get("answer_type") == "yes_no" and x["in_generation"]]
    cnt = Counter(x["expected_verdict"] for x in yn)
    return {"questions": len(yn), "verdicts": dict(cnt), "majority_accuracy": _r(max(cnt.values()) / len(yn)),
            "always_no_accuracy": _r(cnt.get("no", 0) / len(yn))}


# ---------------------------------------------------------------- table 4: cost, latency, spend

def table4(run: Run) -> dict:
    rows = {}
    closed = run.gen["remote|closed|answerable"]
    for c in GEN_CONFIGS:
        g = run.gen.get(f"remote|{c}|answerable")
        if not g:
            continue
        cells = run.cell("remote", c)
        d_cost = (g["cost_per_question"] or 0) - (closed["cost_per_question"] or 0)
        rows[c] = {"score": g["score"], "cost_per_question": g["cost_per_question"],
                   "cost_per_correct": g["cost_per_correct"], "tokens_in_mean": g["tokens_in_mean"],
                   "tokens_out_mean": g["tokens_out_mean"],
                   "reasoning_tokens_mean": _r(np.mean([r["reasoning_tokens"] or 0 for r in cells]), 1),
                   "score_gain_per_usd_vs_closed": None if c == "closed" or d_cost <= 0
                   else _r((g["score"] - closed["score"]) / d_cost, 0)}
    lat = {}
    for a in ANSWERERS:
        for c in GEN_CONFIGS:
            ls = [r["latency_s"] for r in run.cell(a, c) if r["latency_s"] is not None and not r["missing"]]
            if ls:
                lat[f"{a}|{c}"] = {"p50": _r(np.quantile(ls, 0.5), 2), "p95": _r(np.quantile(ls, 0.95), 2)}
    usage = _jsonl(run.dir / "usage.jsonl")
    acc = _jsonl(ROOT / "data" / "questions" / "generation_log" / f"{run.sample}_acceptable.jsonl")
    probe = _jsonl(ROOT / "data" / "processed" / "cutoff_probe" / "judged.jsonl") + \
        _jsonl(ROOT / "data" / "processed" / "cutoff_probe" / "answers.jsonl")
    spend = {
        "answerer_remote (phase C, incl. retries)": sum(u.get("cost_usd") or 0 for u in usage
                                                       if u["phase"] == "C" and u["model"] == "remote"),
        "judge correctness + faithfulness (phase D, incl. re-judging)": sum(j.get("cost_usd") or 0 for j in run.judgments),
        "acceptable_vuids check (Stage 3b)": sum(a.get("cost_usd") or 0 for a in acc),
        "cutoff probe (Stage 2)": sum(p.get("cost_usd") or 0 for p in probe),
    }
    spend = {k: _r(v, 3) for k, v in spend.items()}
    spend["logged total"] = _r(sum(spend.values()), 3)
    return {"remote": rows, "latency": lat, "spend_usd": spend}


# ---------------------------------------------------------------- calibration and length bias

def calibration(run: Run) -> dict:
    from vkrag.eval.annotate import agreement

    d = run.dir / "annotations"
    tune = _jsonl(d / "judge_calibration_tune_annotated.labels.jsonl")
    held = _jsonl(d / "judge_calibration_heldout_annotated.labels.jsonl")
    out = {"tune": agreement(run.run_id, tune), "heldout_revised": agreement(run.run_id, held),
           "pooled_revised": agreement(run.run_id, tune + held),
           # the blind first pass of the held-out labels was overwritten by the revision; values from PLAN §10
           "heldout_blind_first_pass": {"correctness": {"kappa": 0.825, "ci95": [0.634, 0.957]},
                                        "hallucination": {"kappa": 0.658, "ci95": [0.342, 0.908]}}}
    sc = {(r["qid"], r["answerer"], r["config"]): r for r in run.scores}
    human = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}
    pairs = []
    for lab in tune + held:
        s = sc.get((lab["qid"], lab["answerer"], lab["config"]))
        if s:
            pairs.append((s["answer_chars"], human[lab["human"]["correctness"]], s["score"]))
    if pairs:
        from scipy.stats import spearmanr

        L, H, J = map(np.array, zip(*pairs))
        out["length"] = {"n": len(pairs), "rho_len_human": _r(spearmanr(L, H)[0]), "rho_len_judge": _r(spearmanr(L, J)[0]),
                         "rho_len_judge_minus_human": _r(spearmanr(L, J - H)[0]),
                         "mean_human": _r(H.mean()), "mean_judge": _r(J.mean())}
    return out


def length_bias(run: Run) -> dict:
    from scipy.stats import spearmanr

    cells = {}
    for a in ANSWERERS:
        for c in GEN_CONFIGS:
            rows = [r for r in run.cell(a, c) if not r["missing"]]
            if len({r["score"] for r in rows}) > 1:
                cells[f"{a}|{c}"] = _r(spearmanr([r["answer_chars"] for r in rows], [r["score"] for r in rows])[0])
    big = {k: v for k, v in cells.items() if abs(v) > 0.3}
    return {"cells": cells, "abs_rho_gt_0.3": len(big), "negative": sum(v < 0 for v in big.values())}


# ---------------------------------------------------------------- error candidates

def error_candidates(run: Run, per_cat: int = 8) -> dict[str, list[dict]]:
    sc = {(r["qid"], r["answerer"], r["config"]): r for r in run.scores}
    rq = {(r["qid"], r["config"]): r for r in run.ret_q}
    answers = {(a["qid"], a["answerer"], a["config"]): a["answer"] for a in _jsonl(run.dir / "answers.jsonl")
               if a["repeat_idx"] == 0}
    tr = defaultdict(dict)
    for t in _jsonl(run.dir / "query_transforms.jsonl"):
        tr[t["qid"]][t["kind"]] = t
    cats: dict[str, list] = defaultdict(list)
    for (qid, a, c), r in sorted(sc.items()):
        if not r["answerable"] or r["missing"]:
            continue
        ret = rq.get((qid, c))
        if c == "rrf_rerank" and ret and ret["ctx_class"] == 0 and r["score"] < 1:
            cats["retrieval_miss"].append((qid, a, c))
        if c == "rrf_rerank" and ret and ret["ctx_class"] == 1 and r["score"] <= 0.5:
            cats["context_ok_answer_wrong"].append((qid, a, c))
        if c == "closed" and r["stratum"] in ("recent", "ext_niche") and r["score"] == 0 \
                and sc.get((qid, a, "oracle"), {}).get("score") == 1:
            cats["closed_memory_gap"].append((qid, a, c))
        if r.get("scenario_other_violation") or (c == "oracle" and r["score"] < 1):
            cats["question_or_gold_issue"].append((qid, a, c))
    for qid, t in tr.items():
        for kind, conf in (("rewrite", "rewrite_rrf"), ("hyde", "hyde_rrf")):
            x = t.get(kind)
            if x and x.get("unknown_identifiers") and rq.get((qid, conf)) and rq.get((qid, "rrf")) \
                    and rq[(qid, conf)]["class@5"] < rq[(qid, "rrf")]["class@5"]:
                cats["transform_fabricated_identifier"].append((qid, kind, conf))
    out = {}
    for cat, items in cats.items():
        lst = []
        for qid, a, c in items[:per_cat] if cat != "transform_fabricated_identifier" else items:
            q = run.q[qid]
            e = {"qid": qid, "stratum": q["stratum"], "style": q["style"], "answer_type": q.get("answer_type"),
                 "question": q["question"], "reference": q["reference_answer"]}
            if cat == "transform_fabricated_identifier":
                e |= {"kind": a, "config": c, "text": tr[qid][a]["text"][:600],
                      "unknown_identifiers": tr[qid][a]["unknown_identifiers"],
                      "class@5": rq[(qid, c)]["class@5"], "class@5_rrf": rq[(qid, "rrf")]["class@5"]}
            else:
                r = sc[(qid, a, c)]
                e |= {"answerer": a, "config": c, "score": r["score"], "judge": r["judge_reason"],
                      "answer": (answers.get((qid, a, c)) or "")[:700]}
            lst.append(e)
        out[cat] = {"count": len(items), "examples": lst}
    return out


def _write_candidates(cands: dict, path: Path) -> None:
    lines = ["# Error candidates (automatic selection for the Stage 8 error analysis)", "",
             "Generated by `vkrag report`. Categories overlap; counts are answer-level (question x answerer).", ""]
    for cat, d in cands.items():
        lines += [f"## {cat} ({d['count']})", ""]
        for e in d["examples"]:
            head = f"### {e['qid']} — {e['stratum']}, {e['style']}, {e['answer_type']}"
            lines += [head, "", f"**Q:** {e['question']}", "", f"**Reference:** {e['reference']}", ""]
            if "answer" in e:
                lines += [f"**{e['answerer']} / {e['config']}** score {e['score']}; judge: {e['judge']}", "",
                          "```", e["answer"], "```", ""]
            else:
                lines += [f"**{e['kind']}** ({e['config']} class@5 {e['class@5']} vs rrf {e['class@5_rrf']}), "
                          f"unknown: {', '.join(e['unknown_identifiers'])}", "", "```", e["text"], "```", ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- figures

def _style(ax, title: str, xlabel: str | None = None, ylabel: str | None = None) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    if xlabel:
        ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED, fontsize=9)


def figures(data: dict, out_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    # 1. score by stratum: closed / rrf_rerank / oracle, one panel per answerer
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True, facecolor=SURFACE)
    x = np.arange(len(STRATA))
    w = 0.26
    for ax, a in zip(axes, ANSWERERS):
        for i, c in enumerate(("closed", "rrf_rerank", "oracle")):
            d = data["by_stratum"][f"{a}|{c}"]
            m = np.array([d[s]["mean"] for s in STRATA])
            lo = m - np.array([d[s]["ci95"][0] for s in STRATA])
            hi = np.array([d[s]["ci95"][1] for s in STRATA]) - m
            ax.bar(x + (i - 1) * w, m, w - 0.03, color=COLORS[c], label=c, zorder=2)
            ax.errorbar(x + (i - 1) * w, m, yerr=[lo, hi], fmt="none", ecolor=MUTED, elinewidth=1, capsize=2, zorder=3)
        _style(ax, f"{a}: score by stratum (n = 9 per bar, 95% cluster CI)", ylabel="mean score" if a == "qwen" else None)
        ax.set_xticks(x, STRATA)
        ax.set_ylim(0, 1.05)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, frameon=False, fontsize=9, loc="lower center", ncol=3)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    paths.append(out_dir / "score_by_stratum.png")
    fig.savefig(paths[-1], dpi=150)
    plt.close(fig)

    # 2. Recall@k (class) curves
    ks = (1, 3, 5, 10, 20)
    sel = (("bm25", COLORS["closed"], "-"), ("dense", COLORS["oracle"], "-"), ("rrf", COLORS["rrf_rerank"], "-"),
           ("rrf_rerank", COLORS["rrf_rerank"], "--"), ("hyde_rrf", COLORS["extra"], "-"))
    fig, ax = plt.subplots(figsize=(7, 4.2), facecolor=SURFACE)
    for c, col, ls in sel:
        y = [data["table1"][c]["all"][f"class@{k}"] for k in ks]
        ax.plot(ks, y, color=col, linestyle=ls, linewidth=2, marker="o", markersize=5, label=c)
    _style(ax, "Recall@k by equivalence class (90 answerable questions)", "k (log scale)", "class recall@k")
    ax.set_xscale("log")
    ax.set_xticks(ks, [str(k) for k in ks])
    ax.set_xlim(0.9, 22)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    paths.append(out_dir / "recall_at_k.png")
    fig.savefig(paths[-1], dpi=150)
    plt.close(fig)

    # 3. Pareto: remote score vs cost per question
    t4 = data["table4"]["remote"]
    pts = sorted(((v["cost_per_question"] * 1e6, v["score"], c) for c, v in t4.items()), key=lambda p: (p[0], -p[1]))
    front, best = [], -1.0
    for p in pts:  # oracle* are upper bounds, not deployable systems: excluded from the front
        if p[1] > best and not p[2].startswith("oracle"):
            front.append(p)
            best = p[1]
    fig, ax = plt.subplots(figsize=(7.5, 4.5), facecolor=SURFACE)
    fs = {p[2] for p in front}
    for cx, cy, c in pts:
        ax.scatter(cx, cy, s=48, color=COLORS["rrf_rerank"] if c in fs else MUTED, zorder=3,
                   edgecolor=SURFACE, linewidth=1.5)
        off = {"rrf": (-6, -4), "rewrite_rrf_rerank": (6, -11), "hyde_rrf_rerank": (5, 6), "bm25": (5, -11)}.get(c, (5, 4))
        ax.annotate(c, (cx, cy), xytext=off, textcoords="offset points", fontsize=8, color=INK,
                    ha="right" if off[0] < 0 else "left")
    ax.plot([p[0] for p in front], [p[1] for p in front], color=COLORS["rrf_rerank"], linewidth=1.5, zorder=2,
            label="Pareto front (oracle configs excluded)")
    _style(ax, "remote answerer: score vs cost per question", "cost per question, micro-USD", "mean score")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    paths.append(out_dir / "pareto_cost_remote.png")
    fig.savefig(paths[-1], dpi=150)
    plt.close(fig)

    # 4. score vs observed latency p50, both answerers (generation latency only, not phase L)
    fig, ax = plt.subplots(figsize=(7.5, 4.5), facecolor=SURFACE)
    for a, col, mk in (("qwen", COLORS["closed"], "o"), ("remote", COLORS["rrf_rerank"], "s")):
        for c in GEN_CONFIGS:
            k = f"{a}|{c}"
            if k in data["table4"]["latency"]:
                lx, ly = data["table4"]["latency"][k]["p50"], data["table2"][k]["score"]
                ax.scatter(lx, ly, s=40, color=col, marker=mk, edgecolor=SURFACE, linewidth=1.2, zorder=3,
                           label=a if c == "closed" else None)
                if c in ("closed", "rrf_rerank", "oracle"):
                    ax.annotate(c, (lx, ly), xytext=(5, 3), textcoords="offset points", fontsize=7, color=INK)
    _style(ax, "score vs answer latency p50 (generation call only)", "latency p50, s", "mean score")
    ax.legend(frameon=False, fontsize=8, loc="lower center")
    fig.tight_layout()
    paths.append(out_dir / "score_vs_latency.png")
    fig.savefig(paths[-1], dpi=150)
    plt.close(fig)
    return paths


# ---------------------------------------------------------------- markdown tables

def _md(header: list[str], rows: list[list]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + \
        ["| " + " | ".join(str(c) for c in r) + " |" for r in rows] + [""]


def render_tables(d: dict) -> str:
    L = ["# Report tables (generated by `vkrag report`; do not edit by hand)", ""]
    t0 = d["table0"]
    L += ["## Table 0. Corpus and sample", ""]
    L += _md(["item", "value"], [
        ["spec tag", t0["spec_tag"]],
        ["VUs in validusage.json (explicit / total)", f"{t0['explicit_total']:,} / {t0['vu_total']:,}"],
        ["explicit VUIDs mapped to a section", f"{t0['coverage'] * 100:.1f}%"],
        ["differences vs Vulkan-Headers (build-only / headers-only)",
         f"{t0['headers_only_in_build']} / {t0['headers_only_in_headers']}"],
        ["chunks: VU / refpage parts / prose parts",
         f"{t0['chunks_by_type']['vu']:,} / {t0['chunks_by_type']['section_refpage']:,} / {t0['chunks_by_type']['section_prose']:,}"],
        ["chunk tokens p50 / p90 / max: VU", "{p50} / {p90} / {max}".format(**t0["chunk_tokens"]["vu"])],
        ["chunk tokens p50 / p90 / max: refpage", "{p50} / {p90} / {max}".format(**t0["chunk_tokens"]["section_refpage"])],
        ["chunk tokens p50 / p90 / max: prose", "{p50} / {p90} / {max}".format(**t0["chunk_tokens"]["section_prose"])],
        ["explicit equivalence classes (singletons)",
         f"{t0['equivalence']['explicit_classes']:,} ({t0['equivalence']['size_distribution']['1']:,})"],
        ["questions: answerable (identifier / descriptive) + unanswerable",
         f"{t0['questions']['answerable']} ({t0['questions']['style']['identifier']} / {t0['questions']['style']['descriptive']}) + {t0['questions']['unanswerable']}"],
        ["questions in generation (one style per VU) + unanswerable", t0["questions"]["in_generation"]],
        ["answer_type rule / scenario / yes_no", " / ".join(str(t0["questions"]["answer_type"][k]) for k in ("rule", "scenario", "yes_no"))],
        ["descriptive_infeasible", t0["questions"]["descriptive_infeasible"]],
        ["questions with extended acceptable_vuids", t0["questions"]["with_acceptable_vuids"]],
    ])
    L += ["Strata (eligible explicit VUs / sampled VUs in the pilot):", ""]
    L += _md(["stratum", "available", "pilot VUs"], [[s, f"{t0['strata_available'].get(s, 0):,}",
                                                      t0["strata_selected_vus"].get(s, 0)] for s in STRATA])
    L += ["Gold class size of the answerable questions (VU chunks with grade >= 2):", ""]
    gc = t0["questions"]["gold_class_size"]
    L += _md(["class size"] + list(gc), [["questions"] + list(gc.values())])

    L += ["## Table 1. Retrieval (90 answerable questions; ranking before context assembly)", ""]
    rows = []
    for c, v in d["table1"].items():
        a = v["all"]
        rows.append([c, _f(a["strict@5"]), _f(a["class@1"]), _fmt_ci(v["class@5_ci"]), _f(a["class@20"]),
                     _f(a["soft@5"]), _f(a["mrr@10"]), _f(a["ndcg@10"]),
                     _f(v["by_style"]["identifier"]["class@5"]), _f(v["by_style"]["descriptive"]["class@5"]),
                     _f(a["ctx_class"]), _f(v["ctx_types"].get("vu", 0), pct=True),
                     _f(v["ctx_types"].get("refpage", 0), pct=True), _f(v["ctx_types"].get("prose", 0), pct=True)])
    L += _md(["config", "strict@5", "class@1", "class@5 [95% CI]", "class@20", "soft@5", "MRR@10", "nDCG@10",
              "class@5 id", "class@5 desc", "gold in ctx", "ctx VU %", "ctx refpage %", "ctx prose %"], rows)

    L += ["## Table 2. Generation, answerable questions (n = 45 per cell)", ""]
    rows = []
    for k, v in d["table2"].items():
        a, c = k.split("|")
        fa = v.get("faithfulness") or {}
        rows.append([a, c, _fmt_ci(v["score_ci"]), _f(v["correct"]), _f(v["selective_accuracy"]), _f(v["abstain"]),
                     _fmt_ci(v["hallucination_ci"]), _f(v["fabricated_identifier"]), _f(v["fabricated_vuid"]),
                     _f(v["citation_correct"]), _f(v["verdict_match"]), _f(fa.get("supported")),
                     _f(v["self_knowledge"]), _f(v["missing"])])
    L += _md(["answerer", "config", "score [95% CI]", "correct", "selective acc.", "abstain", "hallucination [95% CI]",
              "fabr. ident.", "fabr. VUID", "citation acc.", "yes/no verdict", "faithful", "self-knowl.", "missing"], rows)
    b = d["yes_no_baseline"]
    L += [f"Trivial baseline: majority verdict on the {b['questions']} yes/no questions in generation "
          f"({b['verdicts']}) gives {b['majority_accuracy']:.2f} verdict accuracy, always \"no\" {b['always_no_accuracy']:.2f}.", ""]
    bv = d["bare_verdicts"]
    L += [f"Sensitivity: {bv['rescored_answers']} answers consisting only of the expected \"Yes.\"/\"No.\" were scored "
          "partial by the judge; rescored as correct (cells that change):", ""]
    L += _md(["answerer", "config", "score", "score, bare verdict = correct"],
             [[k.split("|")[0], k.split("|")[1], _f(v["score"], 3), _f(v["score_bare_as_correct"], 3)]
              for k, v in bv["cells"].items() if v["score"] != v["score_bare_as_correct"]])

    L += ["Unanswerable questions (n = 5 per cell): premise rejected (correct) / accepted (incorrect + hallucination) / "
          "partial; abstentions overlap with the other columns", ""]
    rows = [[k.split("|")[0], k.split("|")[1], v["rejected_premise"], v["accepted_premise"], v["partial"], v["abstained"]]
            for k, v in d["unanswerable"].items()]
    L += _md(["answerer", "config", "rejected", "accepted", "partial", "abstained"], rows)

    L += ["Score by stratum (n = 9 per cell, 95% cluster CI):", ""]
    rows = [[k.split("|")[0], k.split("|")[1]] + [_fmt_ci(v[s]) for s in STRATA] for k, v in d["by_stratum"].items()]
    L += _md(["answerer", "config"] + list(STRATA), rows)

    L += ["Score by whether the gold class reached the context (questions in / out, 95% cluster CI):", ""]
    rows = [[k.split("|")[0], k.split("|")[1], v["in"]["n"], _fmt_ci(v["in"]), v.get("out", {}).get("n", 0),
             _fmt_ci(v.get("out"))] for k, v in d["by_gold_in_context"].items()]
    L += _md(["answerer", "config", "n in", "score, gold in context", "n out", "score, gold not in context"], rows)

    L += ["## Table 3. Hypotheses (exploratory; Holm over the 8-test family for reference)", ""]
    rows = []
    for name, t in d["hypotheses"]["tests"].items():
        if name == "H5":
            cq, cc = t["cost_per_question"], t["cost_per_correct"]
            rows.append([name, t["comparison"], "cost_per_correct, USD",
                         f"{cc['a'] * 1e6:.0f}u -> {cc['b'] * 1e6:.0f}u",
                         f"+{cc['diff'] * 1e6:.0f}u [{cc['ci95'][0] * 1e6:.0f}, {cc['ci95'][1] * 1e6:.0f}]",
                         t["p"], t["p_holm"]])
            continue
        rows.append([name, t["comparison"], t["metric"], f"{t['mean_a']:.3f} -> {t['mean_b']:.3f}",
                     f"{t['diff']:+.3f} [{t['ci95'][0]:.3f}, {t['ci95'][1]:.3f}]", t["p"], t["p_holm"]])
    L += _md(["test", "comparison", "metric", "A -> B", "diff [95% CI]", "p", "p_Holm"], rows)
    L += ["(u = micro-USD. H4 p is the one-sided bootstrap non-inferiority p at margin -0.05.)", ""]
    rows = []
    for name, t in d["hypotheses"]["exploratory"].items():
        if "did" in t:
            rows.append([name, f"{t['did']:+.3f}", f"[{t['ci95'][0]:.3f}, {t['ci95'][1]:.3f}]"])
        else:
            rows.append([name, f"{t['diff']:+.3f}", f"[{t['ci95'][0]:.3f}, {t['ci95'][1]:.3f}]"])
    L += _md(["exploratory comparison", "estimate", "95% CI"], rows)
    rows = [[k, v["alpha_0.05"], v["alpha_0.05/8"]] for k, v in d["hypotheses"]["mde_pilot"].items()]
    L += ["MDE at the pilot size (binary outcome, power 0.8):", ""]
    L += _md(["test", "alpha 0.05", "alpha 0.05/8"], rows)

    L += ["## Table 4. Cost (remote answerer) and latency", ""]
    rows = [[c, _f(v["score"]), f"{v['cost_per_question'] * 1e6:.0f}",
             "-" if v["cost_per_correct"] is None else f"{v['cost_per_correct'] * 1e6:.0f}",
             v["tokens_in_mean"], v["tokens_out_mean"], v["reasoning_tokens_mean"],
             "-" if v["score_gain_per_usd_vs_closed"] is None else f"{v['score_gain_per_usd_vs_closed']:,.0f}"]
            for c, v in d["table4"]["remote"].items()]
    L += _md(["config", "score", "cost/question, uUSD", "cost/correct, uUSD", "tokens in", "tokens out",
              "reasoning tokens", "score gain per USD vs closed"], rows)
    lat = d["table4"]["latency"]
    rows = [[c] + [f"{lat[f'{a}|{c}']['p50']:.2f} / {lat[f'{a}|{c}']['p95']:.2f}" if f"{a}|{c}" in lat else "-"
                   for a in ANSWERERS] for c in GEN_CONFIGS]
    L += ["Answer latency p50 / p95, s (generation call only; qwen local sequential, remote through OpenRouter; "
          "no phase L, retrieval time not included):", ""]
    L += _md(["config", "qwen", "remote"], rows)
    L += ["OpenRouter spend logged in the run files, USD:", ""]
    L += _md(["item", "USD"], [[k, f"{v:.3f}"] for k, v in d["table4"]["spend_usd"].items()])

    cal = d["calibration"]
    L += ["## Judge calibration", ""]
    rows = []
    for name in ("tune", "heldout_blind_first_pass", "heldout_revised", "pooled_revised"):
        v = cal[name]
        cell = lambda f: (f"{v[f]['kappa']:.3f} [{v[f]['ci95'][0]:.3f}, {v[f]['ci95'][1]:.3f}]"
                          if f in v and v[f]["kappa"] is not None else "-")
        rows.append([name, v.get("paired", 40), cell("correctness"), cell("hallucination"), cell("abstained")])
    L += _md(["set", "n", "correctness (linear weighted kappa)", "hallucination kappa", "abstained kappa"], rows)
    if "length" in cal:
        ln = cal["length"]
        L += [f"Length (80 labels): rho(len, human) {ln['rho_len_human']}, rho(len, judge) {ln['rho_len_judge']}, "
              f"rho(len, judge - human) {ln['rho_len_judge_minus_human']}; mean score human {ln['mean_human']} vs "
              f"judge {ln['mean_judge']}.", ""]
    lb = d["length_bias"]
    L += [f"Spearman rho(answer length, judge score) per answerer x config: |rho| > 0.3 in {lb['abs_rho_gt_0.3']} "
          f"of {len(lb['cells'])} cells, {lb['negative']} of them negative.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- entry point

def run(run_id: str = "pilot", sample: str = "pilot") -> dict:
    R = Run(run_id, sample)
    data = {"run_id": run_id, "table0": table0(R), "table1": table1(R), "table2": table2(R),
            "unanswerable": unanswerable(R), "by_stratum": by_stratum(R), "by_gold_in_context": by_gold_in_context(R), "yes_no_baseline": yes_no_baseline(R),
            "bare_verdicts": bare_verdicts(R),
            "hypotheses": R.hyp, "table4": table4(R), "calibration": calibration(R), "length_bias": length_bias(R)}
    out = ROOT / "reports"
    (out / "report_data.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "report_tables.md").write_text(render_tables(data), encoding="utf-8")
    figs = figures(data, out / "figures")
    _write_candidates(error_candidates(R), out / "error_candidates.md")
    return {"tables": "reports/report_tables.md", "data": "reports/report_data.json",
            "figures": [str(p.relative_to(ROOT)) for p in figs], "errors": "reports/error_candidates.md"}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
