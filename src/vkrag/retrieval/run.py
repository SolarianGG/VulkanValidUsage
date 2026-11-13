"""Phase B (PLAN §4 Stage 5): retrieval for every question and configuration -> runs/<run_id>/retrieved.jsonl.

Only the embedder and the reranker use the GPU here; Ollama must be unloaded. Configurations that
need query transforms (rewrite / HyDE, phase A) are added once runs/<run_id>/query_transforms.jsonl exists.
Records are cached by (qid, config, config_hash, question_hash); a rerun only fills what is missing.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

from vkrag.config import ROOT, load_config
from vkrag.index.build import IDX, ollama_loaded
from vkrag.retrieval.core import Corpus, Reranker, Searchers, assemble_context, class_key, oracle_context, oracle_distract_context, rrf

BASE_CONFIGS = ("bm25", "dense", "sparse", "rrf", "rrf_sparse", "bm25_rerank", "dense_rerank", "rrf_rerank", "oracle", "oracle_distract")
TRANSFORM_CONFIGS = ("rewrite_rrf", "rewrite_rrf_rerank", "hyde_rrf", "hyde_rrf_rerank", "rewrite_append_rrf_rerank")


def config_hash(name: str, cfg: dict) -> str:
    r = cfg["retrieval"]
    parts = {
        "name": name,
        "depth": r["depth"],
        "k_rrf": r["k_rrf"],
        "k_gen": r["k_gen"],
        "collapse": r.get("collapse_classes", False),
        "rrf_key": "class" if r.get("collapse_classes") else "chunk",
        "raw_depth": r.get("raw_depth"),
        "bm25": cfg["bm25"],
        "embedder": cfg["embedder"],
        "seed": cfg["seed"],
    }
    if "rerank" in name:
        parts["reranker"] = cfg["reranker"]
    if name.startswith(("rewrite", "hyde")):
        from vkrag.retrieval.transform import prompt

        parts["transform"] = {k: prompt(k)[1] for k in ("rewrite", "hyde")} | {"model": cfg["ollama"]["digest"]}
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:12]


def load_questions(sample: str) -> list[dict]:
    from vkrag.questions.freeze import out_path

    return [json.loads(l) for l in open(out_path(sample), encoding="utf-8")]


def _done(path: Path) -> set[tuple]:
    out = set()
    if path.exists():
        for line in open(path, encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue  # a truncated last line is dropped
            out.add((r["qid"], r["config"], r["config_hash"], r["question_hash"]))
    return out


def run(sample: str, run_id: str, configs: tuple[str, ...] = BASE_CONFIGS) -> dict:
    loaded = ollama_loaded()
    if loaded:
        raise RuntimeError(f"Ollama holds {loaded}; phase B needs the GPU (keep_alive=0)")
    cfg = load_config()
    depth, k_rrf, k_gen = cfg["retrieval"]["depth"], cfg["retrieval"]["k_rrf"], cfg["retrieval"]["k_gen"]
    rdir = ROOT / "runs" / run_id
    rdir.mkdir(parents=True, exist_ok=True)
    out_file = rdir / "retrieved.jsonl"
    done = _done(out_file)
    qs = load_questions(sample)
    corpus = Corpus()
    s = Searchers(corpus)
    rr = Reranker(corpus)
    hashes = {c: config_hash(c, cfg) for c in configs}
    todo = [q for q in qs if any((q["qid"], c, hashes[c], q["question_hash"]) not in done for c in configs)]
    stats = {"questions": len(qs), "todo": len(todo), "written": 0}
    if not todo:
        return stats

    from vkrag.index import embed

    t0 = time.time()
    enc = embed.encode_full([q["question"] for q in todo], sparse=True)
    dense_all = np.load(IDX / "dense.npy") if "oracle_distract" in configs else None
    tq: dict[str, list[str]] = {}  # transformed query texts, aligned with todo
    if any(c.split("_")[0] in ("rewrite", "hyde") for c in configs):
        from vkrag.retrieval.transform import load as load_transforms

        tr = load_transforms(run_id)
        for kind in ("rewrite", "hyde"):
            miss = [q["qid"] for q in todo if (q["qid"], kind) not in tr]
            if miss:
                raise RuntimeError(f"phase A missing {kind} for {len(miss)} questions; run `vkrag transform` first")
            tq[kind] = [tr[(q["qid"], kind)]["text"] for q in todo]
        tq["append"] = [f"{q['question']} {r}" for q, r in zip(todo, tq["rewrite"])]
        tenc = {k: embed.encode(v) for k, v in tq.items()}
    fkey = class_key(corpus) if cfg["retrieval"].get("collapse_classes") else None
    timing: dict[str, float] = {}
    with open(out_file, "a", encoding="utf-8") as f:
        for qi, q in enumerate(todo):
            query = q["question"]
            cache: dict[str, list] = {}

            def get(name: str):
                if name in cache:
                    return cache[name]
                t = time.time()
                if name == "bm25":
                    r = s.search_bm25(query, depth)
                elif name == "dense":
                    r = s.search_dense(enc["dense"][qi], depth)
                elif name == "sparse":
                    r = s.search_sparse(enc["sparse"][qi], depth)
                elif name == "rrf":
                    r = rrf([get("bm25"), get("dense")], k_rrf, depth, fkey)
                elif name == "rrf_sparse":
                    r = rrf([get("bm25"), get("dense"), get("sparse")], k_rrf, depth, fkey)
                elif name in ("rewrite_rrf", "rewrite_append_rrf"):
                    kind = "rewrite" if name == "rewrite_rrf" else "append"
                    r = rrf([s.search_bm25(tq[kind][qi], depth), s.search_dense(tenc[kind][qi], depth)], k_rrf, depth, fkey)
                elif name == "hyde_rrf":  # HyDE passage -> dense, original question -> BM25
                    r = rrf([get("bm25"), s.search_dense(tenc["hyde"][qi], depth)], k_rrf, depth, fkey)
                elif name.endswith("_rerank"):  # the reranker always gets the original question
                    r = rr.rerank(query, get(name.removesuffix("_rerank")), depth)
                else:
                    raise KeyError(name)
                timing[name] = timing.get(name, 0.0) + time.time() - t
                cache[name] = r
                return r

            for c in configs:
                key = (q["qid"], c, hashes[c], q["question_hash"])
                if key in done:
                    continue
                extra = {}
                if c == "oracle":
                    if q["stratum"] == "unanswerable":
                        continue
                    ranked, ctx = None, oracle_context(q, corpus)
                elif c == "oracle_distract":
                    if q["stratum"] == "unanswerable":
                        continue
                    ctx, level = oracle_distract_context(q, corpus, dense_all, cfg["seed"])
                    ranked, extra = None, {"distractor_level": level, "distractors_short": len(ctx) < 6}
                else:
                    ranked = get(c)
                    ctx = assemble_context(ranked, corpus, k_gen)
                rec = {
                    "qid": q["qid"],
                    "config": c,
                    "config_hash": hashes[c],
                    "question_hash": q["question_hash"],
                    "ranked": [[d, round(sc, 6)] for d, sc in ranked] if ranked is not None else None,
                    "context": ctx,
                    **extra,
                }
                f.write(json.dumps(rec) + "\n")
                stats["written"] += 1
            f.flush()
    stats["seconds"] = round(time.time() - t0, 1)
    stats["seconds_by_retriever"] = {k: round(v, 1) for k, v in timing.items()}
    _manifest(rdir, sample, cfg, hashes)
    return stats


def _manifest(rdir: Path, sample: str, cfg: dict, hashes: dict) -> None:
    from vkrag.questions.freeze import out_path

    p = rdir / "manifest.json"
    man = json.load(open(p, encoding="utf-8")) if p.exists() else {}
    qman = json.load(open(out_path(sample).with_suffix(".manifest.json"), encoding="utf-8"))
    iman = json.load(open(IDX / "manifest.json", encoding="utf-8"))
    man.update(
        {
            "sample": sample,
            "questions_sha256": qman["sha256"],
            "corpus_hash": iman["corpus_hash"],
            "index": {k: iman.get(k) for k in ("bm25", "dense_sparse")},
            "retrieval": cfg["retrieval"],
            "reranker": cfg["reranker"],
            "embedder": cfg["embedder"],
        }
    )
    man.setdefault("config_hashes", {}).update(hashes)
    p.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
