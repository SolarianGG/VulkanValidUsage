"""Simulation-based power analysis from the pilot (PLAN §7.4, §9.3).

For each confirmatory comparison (§7.5) a per-question table of binary outcomes (A, B) and entity
clusters is built from the pilot. One simulation:
1. resample pilot entities with replacement until the main-run number of questions is reached;
2. make the null true by a random sign flip per cluster (swap A and B for all questions of the
   cluster): discordance and clustering are kept, the expected difference is 0;
3. inject the effect: B outcomes 0 -> 1 with probability Δ / P(B = 0), so E[B - A] rises by Δ;
4. cluster sign-flip permutation test on the sum of paired differences (two-sided).
MDE = the smallest Δ (1 pp steps) where the test rejects at α = 0.05 / 8 (worst-case Holm) in ≥ 80%
of simulations. H4 (non-inferiority): share of simulations with true difference 0 where the lower
bound of the cluster bootstrap 95% CI of (qwen - remote) is above the margin.
"""
from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

from vkrag.config import PROCESSED, ROOT, load_config

ALPHA = 0.05 / 8
POWER = 0.8


def _clusters(rows: list[tuple[str, int, int]]) -> list[np.ndarray]:
    """rows (entity, a, b) -> per-entity arrays of (a, b)."""
    by = defaultdict(list)
    for e, a, b in rows:
        by[e].append((a, b))
    return [np.array(v, dtype=float) for v in by.values()]


def _resample(cl: list[np.ndarray], n_q: int, rng) -> list[np.ndarray]:
    out, n = [], 0
    while n < n_q:
        c = cl[rng.integers(len(cl))]
        out.append(c)
        n += len(c)
    return out


def _cluster_sums(cl: list[np.ndarray], delta: float, rng) -> np.ndarray:
    """Null by cluster sign flip, then the injected effect; returns per-cluster sums of (B - A)."""
    sums = np.empty(len(cl))
    flipped = [c[:, ::-1] if rng.random() < 0.5 else c for c in cl]
    allb = np.concatenate([c[:, 1] for c in flipped])
    p_b0 = max(1e-9, 1 - allb.mean())
    p = min(1.0, delta / p_b0)
    for i, c in enumerate(flipped):
        b = c[:, 1].copy()
        if p > 0:
            up = (b == 0) & (rng.random(len(b)) < p)
            b[up] = 1
        sums[i] = (b - c[:, 0]).sum()
    return sums


def _perm_p(sums: np.ndarray, n_perm: int, rng) -> float:
    signs = rng.choice((-1.0, 1.0), size=(n_perm, len(sums)))
    t0 = abs(sums.sum())
    t = np.abs(signs @ sums)
    return (1 + (t >= t0 - 1e-12).sum()) / (n_perm + 1)


def power_at(cl, n_q, delta, n_sim, n_perm, rng) -> float:
    rej = 0
    for _ in range(n_sim):
        s = _cluster_sums(_resample(cl, n_q, rng), delta, rng)
        rej += _perm_p(s, n_perm, rng) < ALPHA
    return rej / n_sim


def mde(cl, n_q, n_sim, n_perm, rng, max_delta=0.40) -> dict:
    curve = {}
    lo_d = None
    for d in np.arange(0.01, max_delta + 1e-9, 0.01):
        pw = power_at(cl, n_q, d, max(200, n_sim // 4), n_perm, rng)  # coarse pass
        curve[round(d, 2)] = round(pw, 3)
        if pw >= POWER:
            lo_d = d
            break
    if lo_d is None:
        return {"mde": None, "curve": curve}
    # confirm with the full number of simulations (step back while still powered)
    d = lo_d
    while d > 0.01 and power_at(cl, n_q, d - 0.01, n_sim, n_perm, rng) >= POWER:
        d -= 0.01
    final = power_at(cl, n_q, d, n_sim, n_perm, rng)
    if final < POWER:
        d += 0.01
        final = power_at(cl, n_q, d, n_sim, n_perm, rng)
    return {"mde": round(d, 2), "power_at_mde": round(final, 3), "coarse_curve": curve}


def ni_power(cl, n_q, margin, n_sim, n_boot, rng) -> float:
    ok = 0
    for _ in range(n_sim):
        res = _resample(cl, n_q, rng)
        s = _cluster_sums(res, 0.0, rng)
        n = np.array([len(c) for c in res], dtype=float)
        idx = rng.integers(len(s), size=(n_boot, len(s)))
        diffs = s[idx].sum(axis=1) / n[idx].sum(axis=1)
        ok += np.quantile(diffs, 0.025) > margin
    return ok / n_sim


def descriptives(rows) -> dict:
    a = np.array([r[1] for r in rows], dtype=float)
    b = np.array([r[2] for r in rows], dtype=float)
    cl = _clusters(rows)
    return {"questions": len(rows), "entities": len(cl), "mean_a": round(a.mean(), 3), "mean_b": round(b.mean(), 3),
            "discordant": round(float((a != b).mean()), 3), "b_minus_a": round(float((b - a).mean()), 3),
            "questions_per_entity": round(len(rows) / len(cl), 2)}


# ---------------------------------------------------------------- pilot tables

def _entities(sample: str) -> dict[str, str]:
    from vkrag.retrieval.run import load_questions

    return {q["qid"]: q.get("entity") or q["qid"] for q in load_questions(sample)}


def generation_rows(run_id: str, ent: dict, a_key: tuple[str, str], b_key: tuple[str, str],
                    outcome: str = "correct") -> list[tuple[str, int, int]]:
    by = defaultdict(dict)
    for line in open(ROOT / "runs" / run_id / "scores.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r["answerable"] and r.get("correctness") is not None and r["repeat_idx"] == 0:
            v = r["score"] == 1.0 if outcome == "correct" else r["score"]
            by[r["qid"]][(r["answerer"], r["config"])] = v
    return [(ent[q], int(d[a_key]), int(d[b_key])) for q, d in by.items() if a_key in d and b_key in d]


def retrieval_rows(run_id: str, ent: dict, a: str, b: str, metric: str = "class@5") -> list[tuple[str, int, int]]:
    by = defaultdict(dict)
    for line in open(ROOT / "runs" / run_id / "retrieval_metrics_per_question.jsonl", encoding="utf-8"):
        r = json.loads(line)
        by[r["qid"]][r["config"]] = r[metric]
    return [(ent[q], int(d[a]), int(d[b])) for q, d in by.items() if a in d and b in d]


def run(sample: str = "pilot", run_id: str = "pilot", n_sim: int = 2000, n_perm: int = 2000, n_boot: int = 1000) -> dict:
    cfg = load_config()
    rng = np.random.default_rng(cfg["seed"])
    ent = _entities(sample)
    samples = json.load(open(PROCESSED / "samples.json", encoding="utf-8"))
    n_main_vu = len(samples["main"]) if isinstance(samples["main"], list) else cfg["strata"]["per_stratum"] * 5
    comps = {
        # retrieval: both styles of every VU (2 questions per VU)
        "H2a rrf vs bm25 (class@5)": ("retrieval", ("bm25", "rrf"), 2 * n_main_vu),
        "H2b rrf vs dense (class@5)": ("retrieval", ("dense", "rrf"), 2 * n_main_vu),
        "H3a rrf_rerank vs rrf (class@5)": ("retrieval", ("rrf", "rrf_rerank"), 2 * n_main_vu),
        # generation: one style per VU
        "H1a qwen rrf_rerank vs closed": ("generation", (("qwen", "closed"), ("qwen", "rrf_rerank")), n_main_vu),
        "H1b remote rrf_rerank vs closed": ("generation", (("remote", "closed"), ("remote", "rrf_rerank")), n_main_vu),
    }
    out = {"alpha": ALPHA, "target_power": POWER, "n_sim": n_sim, "n_perm": n_perm, "main_vus": n_main_vu, "comparisons": {}}
    for name, (kind, (a, b), n_q) in comps.items():
        rows = retrieval_rows(run_id, ent, a, b) if kind == "retrieval" else generation_rows(run_id, ent, a, b)
        if not rows:
            out["comparisons"][name] = {"error": "no pilot data"}
            continue
        cl = _clusters(rows)
        out["comparisons"][name] = descriptives(rows) | {"main_questions": n_q} | mde(cl, n_q, n_sim, n_perm, rng)
        print(name, out["comparisons"][name].get("mde"))
    # H3b: rrf_rerank vs rrf, both answerers pooled; cluster = entity (both answerers inside)
    rows = [(e, a, b) for m in ("qwen", "remote")
            for e, a, b in generation_rows(run_id, ent, (m, "rrf"), (m, "rrf_rerank"))]
    if rows:
        cl = _clusters(rows)
        out["comparisons"]["H3b rrf_rerank vs rrf (score, both answerers)"] = (
            descriptives(rows) | {"main_questions": 2 * n_main_vu} | mde(cl, 2 * n_main_vu, n_sim, n_perm, rng))
    # H4: qwen rrf_rerank vs remote closed, non-inferiority at true difference 0
    rows = generation_rows(run_id, ent, ("remote", "closed"), ("qwen", "rrf_rerank"))
    if rows:
        cl = _clusters(rows)
        margin = cfg["eval"]["ni_margin"]
        out["comparisons"]["H4 qwen rrf_rerank vs remote closed (NI)"] = descriptives(rows) | {
            "margin": margin, "main_questions": n_main_vu,
            "p_confirm_ni_at_true_diff_0": round(ni_power(cl, n_main_vu, margin, n_sim, n_boot, rng), 3)}
    (ROOT / "runs" / run_id / "power.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return out
