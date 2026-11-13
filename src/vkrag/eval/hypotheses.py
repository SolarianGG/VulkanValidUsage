"""Hypothesis tests on the final (pilot) run, PLAN §7.4-7.5 as amended in §10 (2026-11-10): all
comparisons are exploratory; Holm-adjusted p-values over the 8-test family are given for reference.

Every comparison is paired by question and clustered by entity:
- effect = mean(B - A) over questions; 95% CI by cluster bootstrap (entities resampled with all their
  questions in both arms);
- p-value: cluster sign-flip permutation test (the A/B labels of all questions of an entity are swapped
  together), two-sided, Monte Carlo;
- H4 (non-inferiority, qwen rrf_rerank - remote closed): the lower bound of the 95% CI against the
  margin; one-sided p = share of bootstrap differences <= margin;
- H5: cost_per_question and cost_per_correct (= sum cost / sum score) of remote rrf_rerank vs closed;
  the permutation swaps (cost, score) pairs per cluster, the statistic is the difference of ratios.
MDE at the pilot size comes from `power.mde` (same simulation as before the run) at α = 0.05 and at
α = 0.05 / 8.
"""

from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

from vkrag.config import ROOT, load_config
from vkrag.eval import power as P

FAMILY = ("H1a", "H1b", "H2a", "H2b", "H3a", "H3b", "H4", "H5")


# ---------------------------------------------------------------- data


def _scores(run_id: str) -> dict[str, dict]:
    """qid -> {"entity", "stratum", "style", (answerer, config): row} for answerable questions."""
    by: dict[str, dict] = defaultdict(dict)
    for line in open(ROOT / "runs" / run_id / "scores.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r["answerable"] and r["repeat_idx"] == 0:
            d = by[r["qid"]]
            d.update(entity=r["entity"], stratum=r["stratum"], style=r["style"])
            d[(r["answerer"], r["config"])] = r
    return by


def _retrieval(run_id: str, ent: dict[str, str]) -> dict[str, dict]:
    by: dict[str, dict] = defaultdict(dict)
    for line in open(ROOT / "runs" / run_id / "retrieval_metrics_per_question.jsonl", encoding="utf-8"):
        r = json.loads(line)
        d = by[r["qid"]]
        d.update(entity=ent[r["qid"]], stratum=r["stratum"], style=r["style"])
        d[r["config"]] = r
    return by


def gen_rows(sc: dict, a: tuple[str, str], b: tuple[str, str], binary: bool = False) -> list[tuple[str, float, float]]:
    f = (lambda r: float(r["score"] == 1.0)) if binary else (lambda r: float(r["score"]))
    return [(d["entity"], f(d[a]), f(d[b])) for d in sc.values() if a in d and b in d]


def ret_rows(rt: dict, a: str, b: str, metric: str = "class@5") -> list[tuple[str, float, float]]:
    return [(d["entity"], float(d[a][metric]), float(d[b][metric])) for d in rt.values() if a in d and b in d]


# ---------------------------------------------------------------- statistics


def _arrays(rows):
    cl = P._clusters(rows)  # per-entity arrays of (a, b)
    diff = np.array([(c[:, 1] - c[:, 0]).sum() for c in cl])
    n = np.array([len(c) for c in cl], dtype=float)
    return cl, diff, n


def paired(rows, n_boot: int, n_perm: int, rng) -> dict:
    """Mean paired difference B - A with cluster bootstrap CI and cluster sign-flip permutation p."""
    cl, s, n = _arrays(rows)
    est = s.sum() / n.sum()
    idx = rng.integers(len(s), size=(n_boot, len(s)))
    boots = s[idx].sum(axis=1) / n[idx].sum(axis=1)
    signs = rng.choice((-1.0, 1.0), size=(n_perm, len(s)))
    t = np.abs(signs @ s)
    p = (1 + (t >= abs(s.sum()) - 1e-12).sum()) / (n_perm + 1)
    a = np.concatenate([c[:, 0] for c in cl])
    b = np.concatenate([c[:, 1] for c in cl])
    return {
        "questions": int(n.sum()),
        "entities": len(cl),
        "mean_a": round(float(a.mean()), 4),
        "mean_b": round(float(b.mean()), 4),
        "diff": round(float(est), 4),
        "ci95": [round(float(np.quantile(boots, 0.025)), 4), round(float(np.quantile(boots, 0.975)), 4)],
        "p": round(float(p), 5),
        "discordant": round(float((a != b).mean()), 3),
        "_boots": boots,
    }


def did(rows_by_group: dict[str, list], g1: str, g0: str, n_boot: int, rng) -> dict:
    """Difference of mean paired differences between two disjoint question groups (cluster bootstrap
    within each group). rows: (entity, a, b)."""
    out = {}
    for g in (g1, g0):
        cl, s, n = _arrays(rows_by_group[g])
        idx = rng.integers(len(s), size=(n_boot, len(s)))
        out[g] = (s.sum() / n.sum(), s[idx].sum(axis=1) / n[idx].sum(axis=1), int(n.sum()))
    d = out[g1][1] - out[g0][1]
    return {
        g1: {"diff": round(float(out[g1][0]), 4), "questions": out[g1][2]},
        g0: {"diff": round(float(out[g0][0]), 4), "questions": out[g0][2]},
        "did": round(float(out[g1][0] - out[g0][0]), 4),
        "ci95": [round(float(np.quantile(d, 0.025)), 4), round(float(np.quantile(d, 0.975)), 4)],
    }


def did_paired(rows: list[tuple[str, float, float]], n_boot: int, rng) -> dict:
    """Interaction on paired questions: rows (entity, d_group1, d_group0) per VU, both values inside
    the same cluster; effect = mean(d1 - d0)."""
    cl = P._clusters(rows)
    s = np.array([(c[:, 0] - c[:, 1]).sum() for c in cl])
    n = np.array([len(c) for c in cl], dtype=float)
    idx = rng.integers(len(s), size=(n_boot, len(s)))
    boots = s[idx].sum(axis=1) / n[idx].sum(axis=1)
    return {
        "pairs": int(n.sum()),
        "entities": len(cl),
        "did": round(float(s.sum() / n.sum()), 4),
        "ci95": [round(float(np.quantile(boots, 0.025)), 4), round(float(np.quantile(boots, 0.975)), 4)],
    }


def cost_test(sc: dict, a: tuple[str, str], b: tuple[str, str], n_boot: int, n_perm: int, rng) -> dict:
    """H5: per-cluster sums of cost and score in both arms."""
    by = defaultdict(lambda: np.zeros(4))  # cost_a, score_a, cost_b, score_b
    nq = 0
    for d in sc.values():
        if a in d and b in d:
            nq += 1
            by[d["entity"]] += [d[a]["cost_usd"] or 0.0, d[a]["score"], d[b]["cost_usd"] or 0.0, d[b]["score"]]
    m = np.array(list(by.values()))
    cnt = defaultdict(int)
    for d in sc.values():
        if a in d and b in d:
            cnt[d["entity"]] += 1
    n = np.array([cnt[e] for e in by], dtype=float)

    def stats(mm, nn):
        cpq = (mm[..., 2].sum(-1) - mm[..., 0].sum(-1)) / nn.sum(-1)
        cpc_a = mm[..., 0].sum(-1) / mm[..., 1].sum(-1)
        cpc_b = mm[..., 2].sum(-1) / mm[..., 3].sum(-1)
        return cpq, cpc_a, cpc_b

    cpq, cpc_a, cpc_b = stats(m, n)
    idx = rng.integers(len(m), size=(n_boot, len(m)))
    bq, ba, bb = stats(m[idx], n[idx])
    # permutation: swap arms per cluster
    flip = rng.random((n_perm, len(m))) < 0.5
    mp = np.where(flip[..., None], m[None][..., [2, 3, 0, 1]], m[None])
    _, pa, pb = stats(mp, np.broadcast_to(n, flip.shape))
    t0 = abs(cpc_b - cpc_a)
    p_cpc = (1 + (np.abs(pb - pa) >= t0 - 1e-15).sum()) / (n_perm + 1)
    return {
        "questions": nq,
        "entities": len(m),
        "cost_per_question": {
            "a": round(float(m[:, 0].sum() / n.sum()), 7),
            "b": round(float(m[:, 2].sum() / n.sum()), 7),
            "diff": round(float(cpq), 7),
            "ci95": [round(float(np.quantile(bq, 0.025)), 7), round(float(np.quantile(bq, 0.975)), 7)],
        },
        "cost_per_correct": {
            "a": round(float(cpc_a), 7),
            "b": round(float(cpc_b), 7),
            "diff": round(float(cpc_b - cpc_a), 7),
            "ci95": [round(float(np.quantile(bb - ba, 0.025)), 7), round(float(np.quantile(bb - ba, 0.975)), 7)],
        },
        "p": round(float(p_cpc), 5),
    }


def holm(ps: dict[str, float]) -> dict[str, float]:
    order = sorted(ps, key=ps.get)
    out, run_max = {}, 0.0
    for i, k in enumerate(order):
        run_max = max(run_max, min(1.0, (len(order) - i) * ps[k]))
        out[k] = round(run_max, 5)
    return out


def _mde(rows, n_sim: int, n_perm: int, rng) -> dict:
    cl = P._clusters(rows)
    n_q = sum(len(c) for c in cl)
    out = {}
    for name, alpha in (("alpha_0.05", 0.05), ("alpha_0.05/8", 0.05 / 8)):
        P.ALPHA = alpha
        out[name] = P.mde(cl, n_q, n_sim, n_perm, rng, max_delta=0.6).get("mde")
    P.ALPHA = 0.05 / 8
    return out


# ---------------------------------------------------------------- run


def run(run_id: str = "pilot", sample: str = "pilot", n_sim: int = 1000, n_perm_mde: int = 1000) -> dict:
    cfg = load_config()
    rng = np.random.default_rng(cfg["seed"])
    nb, npm = cfg["eval"]["bootstrap"], cfg["eval"]["permutations"]
    margin = cfg["eval"]["ni_margin"]
    sc = _scores(run_id)
    ent = P._entities(sample)
    rt = _retrieval(run_id, ent)
    Q, R = ("qwen", "rrf_rerank"), ("remote", "rrf_rerank")
    out: dict = {
        "run_id": run_id,
        "status": "exploratory (PLAN §10, 2026-11-10)",
        "bootstrap": nb,
        "permutations": npm,
        "tests": {},
        "sensitivity_binary": {},
        "exploratory": {},
        "mde_pilot": {},
    }
    T = out["tests"]

    def gen(name, a, b, desc):
        r = gen_rows(sc, a, b)
        T[name] = {"comparison": desc, "metric": "score"} | paired(r, nb, npm, rng)
        out["sensitivity_binary"][name] = {k: v for k, v in paired(gen_rows(sc, a, b, True), nb, npm, rng).items() if k != "_boots"}
        out["mde_pilot"][name] = _mde(gen_rows(sc, a, b, True), n_sim, n_perm_mde, rng)

    def ret(name, a, b, desc):
        r = ret_rows(rt, a, b)
        T[name] = {"comparison": desc, "metric": "class@5"} | paired(r, nb, npm, rng)
        out["mde_pilot"][name] = _mde(r, n_sim, n_perm_mde, rng)

    gen("H1a", ("qwen", "closed"), Q, "qwen rrf_rerank vs closed")
    gen("H1b", ("remote", "closed"), R, "remote rrf_rerank vs closed")
    ret("H2a", "bm25", "rrf", "rrf vs bm25")
    ret("H2b", "dense", "rrf", "rrf vs dense")
    ret("H3a", "rrf", "rrf_rerank", "rrf_rerank vs rrf")
    T["H3a"]["criterion_min_gain"] = cfg["eval"]["rerank_min_gain"]
    # H3b: both answerers pooled; a question contributes one pair per answerer inside its entity cluster
    pooled = gen_rows(sc, ("qwen", "rrf"), Q) + gen_rows(sc, ("remote", "rrf"), R)
    T["H3b"] = {
        "comparison": "rrf_rerank vs rrf, both answerers",
        "metric": "score",
        "latency_condition": "not measured (phase L dropped)",
    } | paired(pooled, nb, npm, rng)
    out["sensitivity_binary"]["H3b"] = {
        k: v
        for k, v in paired(gen_rows(sc, ("qwen", "rrf"), Q, True) + gen_rows(sc, ("remote", "rrf"), R, True), nb, npm, rng).items()
        if k != "_boots"
    }
    out["mde_pilot"]["H3b"] = _mde(
        gen_rows(sc, ("qwen", "rrf"), Q, True) + gen_rows(sc, ("remote", "rrf"), R, True), n_sim, n_perm_mde, rng
    )
    # H4: non-inferiority of qwen rrf_rerank against remote closed
    h4 = {"comparison": "qwen rrf_rerank - remote closed (non-inferiority)", "metric": "score", "margin": margin} | paired(
        gen_rows(sc, ("remote", "closed"), Q), nb, npm, rng
    )
    h4["p_superiority_two_sided"] = h4.pop("p")
    h4["p"] = round(float((h4["_boots"] <= margin).mean()), 5)  # one-sided NI p (bootstrap)
    h4["ni_holds"] = h4["ci95"][0] > margin
    T["H4"] = h4
    out["sensitivity_binary"]["H4"] = {
        k: v for k, v in paired(gen_rows(sc, ("remote", "closed"), Q, True), nb, npm, rng).items() if k != "_boots"
    }
    T["H5"] = {"comparison": "remote rrf_rerank vs closed (cost)"} | cost_test(sc, ("remote", "closed"), R, nb, npm, rng)

    ph = holm({k: T[k]["p"] for k in FAMILY})
    for k in FAMILY:
        T[k].pop("_boots", None)
        T[k]["p_holm"] = ph[k]
    T["H1a"]["direction_ok"] = T["H1a"]["diff"] > 0
    T["H1b"]["direction_ok"] = T["H1b"]["diff"] > 0
    for k in ("H2a", "H2b", "H3b"):
        T[k]["direction_ok"] = T[k]["diff"] > 0
    T["H3a"]["direction_ok"] = T["H3a"]["diff"] >= T["H3a"]["criterion_min_gain"]
    c = T["H5"]
    c["direction_ok"] = c["cost_per_question"]["ci95"][0] > 0 and c["cost_per_correct"]["ci95"][1] < 0

    # exploratory
    E = out["exploratory"]
    for m in ("qwen", "remote"):
        groups = {"recent+ext_niche": [], "core_1_0": []}
        for d in sc.values():
            g = "recent+ext_niche" if d["stratum"] in ("recent", "ext_niche") else "core_1_0" if d["stratum"] == "core_1_0" else None
            if g and (m, "closed") in d and (m, "rrf_rerank") in d:
                groups[g].append((d["entity"], float(d[(m, "closed")]["score"]), float(d[(m, "rrf_rerank")]["score"])))
        E[f"H1 DiD {m}: (rrf_rerank - closed) recent+ext_niche vs core_1_0"] = did(groups, "recent+ext_niche", "core_1_0", nb, rng)
        r = paired(gen_rows(sc, (m, "rrf_rerank"), (m, "oracle")), nb, npm, rng)
        r.pop("_boots")
        E[f"oracle - rrf_rerank ({m}, retrieval loss)"] = r
    # H2 interaction: per VU, (rrf - bm25) on the descriptive question minus on the identifier one
    vu = defaultdict(dict)
    qs = {q["qid"]: q for q in __import__("vkrag.retrieval.run", fromlist=["load_questions"]).load_questions(sample)}
    for qid, d in rt.items():
        if "rrf" in d and "bm25" in d and qid in qs:
            vu[qs[qid]["vuid"]][d["style"]] = (d["entity"], d["rrf"]["class@5"] - d["bm25"]["class@5"])
    rows = [(v["descriptive"][0], v["descriptive"][1], v["identifier"][1]) for v in vu.values() if "descriptive" in v and "identifier" in v]
    E["H2 interaction: (rrf - bm25) class@5, descriptive - identifier"] = did_paired(rows, nb, rng)
    for v in out["sensitivity_binary"].values():
        v.pop("_boots", None)
    (ROOT / "runs" / run_id / "hypotheses.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
