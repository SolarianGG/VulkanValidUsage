"""Stage 4: BM25, dense and sparse indexes over all chunks (sections without VU blocks + VU chunks).

Outputs in data/processed/index/ (gitignored):
  doc_ids.json        chunk_id per row, in chunks.jsonl order (shared by all three indexes)
  bm25/               bm25s index over `index_text`, own tokenizer (index/tokenize.py)
  dense.npy           bge-m3 normalized dense vectors (float32), dense.faiss = IndexFlatIP over them
  sparse.npz          bge-m3 lexical weights as a CSR matrix (rows = chunks, cols = XLM-R token ids)
  manifest.json       corpus hash, model revisions, parameters, sizes, timings
Ollama must not hold the GPU while the dense pass runs (checked by `ollama ps`).
"""
from __future__ import annotations

import json
import subprocess
import time

import numpy as np

from vkrag.config import PROCESSED, load_config
from vkrag.index.tokenize import tokenize

IDX = PROCESSED / "index"


def load_chunks() -> list[dict]:
    return [json.loads(l) for l in open(PROCESSED / "chunks.jsonl", encoding="utf-8")]


def ollama_loaded() -> list[str]:
    try:
        out = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [l.split()[0] for l in out.splitlines()[1:] if l.strip()]


def build_bm25(chunks: list[dict], cfg: dict) -> dict:
    import bm25s

    t = time.time()
    toks = [tokenize(c["index_text"]) for c in chunks]
    r = bm25s.BM25(k1=cfg["bm25"]["k1"], b=cfg["bm25"]["b"], method="lucene")
    r.index(toks, show_progress=False)
    r.save(str(IDX / "bm25"), show_progress=False)
    return {"seconds": round(time.time() - t, 1), "vocab": len(r.vocab_dict), "avg_doc_tokens": round(float(np.mean([len(x) for x in toks])), 1)}


def build_dense_sparse(chunks: list[dict]) -> dict:
    import faiss
    import scipy.sparse as sp

    from vkrag.index import embed

    t = time.time()
    res = embed.encode_full([c["index_text"] for c in chunks], sparse=True)
    dense = res["dense"]
    np.save(IDX / "dense.npy", dense)
    index = faiss.IndexFlatIP(dense.shape[1])
    index.add(dense)
    faiss.write_index(index, str(IDX / "dense.faiss"))
    rows, cols, vals = [], [], []
    for i, w in enumerate(res["sparse"]):
        for k, v in w.items():
            rows.append(i)
            cols.append(k)
            vals.append(v)
    vocab = embed.model().tokenizer.vocab_size
    m = sp.csr_matrix((np.asarray(vals, dtype=np.float32), (rows, cols)), shape=(len(chunks), vocab))
    sp.save_npz(IDX / "sparse.npz", m)
    norms = np.linalg.norm(dense, axis=1)
    return {"seconds": round(time.time() - t, 1), "dim": int(dense.shape[1]), "norm_min": round(float(norms.min()), 4),
            "norm_max": round(float(norms.max()), 4), "sparse_nnz_mean": round(m.nnz / len(chunks), 1)}


def build(which: str = "all") -> dict:
    cfg = load_config()
    IDX.mkdir(parents=True, exist_ok=True)
    chunks = load_chunks()
    doc_ids = [c["chunk_id"] for c in chunks]
    (IDX / "doc_ids.json").write_text(json.dumps(doc_ids), encoding="utf-8")
    man_path = IDX / "manifest.json"
    man = json.load(open(man_path, encoding="utf-8")) if man_path.exists() else {}
    cov = json.load(open(PROCESSED / "coverage_report.json", encoding="utf-8"))
    man.update({"corpus_hash": cov["corpus_hash"], "n_docs": len(doc_ids),
                "by_type": {t: sum(c["type"] == t for c in chunks) for t in ("section", "vu")}})
    if which in ("all", "bm25"):
        man["bm25"] = {**build_bm25(chunks, cfg), "k1": cfg["bm25"]["k1"], "b": cfg["bm25"]["b"], "method": "lucene",
                       "tokenizer": "vkrag.index.tokenize (identifiers whole + parts, stop words, Snowball english)"}
    if which in ("all", "dense"):
        loaded = ollama_loaded()
        if loaded:
            raise RuntimeError(f"Ollama holds models {loaded}; unload them first (keep_alive=0)")
        e = cfg["embedder"]
        man["dense_sparse"] = {**build_dense_sparse(chunks), "model": e["model"], "revision": e["revision"],
                               "max_length": e["max_length"], "fp16": e["fp16"], "batch_size": e["batch_size"]}
    man_path.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    return man
