"""Stage 5 retrieval primitives (PLAN §4 Stage 5): BM25 with alias expansion, dense, sparse, RRF,
reranking, context assembly with equivalence-class deduplication, oracle contexts."""

from __future__ import annotations

import json
import random
import re
from functools import cached_property

import numpy as np

from vkrag.config import PROCESSED, load_config
from vkrag.index.build import IDX
from vkrag.index.tokenize import TOKEN, is_identifier, tokenize

Ranked = list[tuple[str, float]]


class Corpus:
    """Chunks, doc order shared with the indexes, aliases."""

    def __init__(self) -> None:
        self.doc_ids: list[str] = json.load(open(IDX / "doc_ids.json", encoding="utf-8"))
        self.row = {d: i for i, d in enumerate(self.doc_ids)}
        self.chunks: dict[str, dict] = {}
        for line in open(PROCESSED / "chunks.jsonl", encoding="utf-8"):
            c = json.loads(line)
            self.chunks[c["chunk_id"]] = c
        al = json.load(open(PROCESSED / "aliases.json", encoding="utf-8"))
        self.alias_to_target: dict[str, str] = al["alias_to_target"]
        self.target_to_aliases: dict[str, list[str]] = al["target_to_aliases"]
        self.sections: dict[str, list[str]] = {}
        for c in self.chunks.values():
            if c["type"] == "section":
                self.sections.setdefault(c["section_id"], []).append(c["chunk_id"])
        for v in self.sections.values():
            v.sort(key=lambda cid: self.chunks[cid]["part_idx"])

    def alias_names(self, name: str) -> set[str]:
        target = self.alias_to_target.get(name, name)
        names = {target, *self.target_to_aliases.get(target, [])}
        names.discard(name)
        return names

    def text(self, cid: str, field: str = "index_text") -> str:
        return self.chunks[cid][field]


class Searchers:
    def __init__(self, corpus: Corpus) -> None:
        self.c = corpus
        self.cfg = load_config()

    @cached_property
    def bm25(self):
        import bm25s

        return bm25s.BM25.load(str(IDX / "bm25"))

    @cached_property
    def dense_index(self):
        import faiss

        return faiss.read_index(str(IDX / "dense.faiss"))

    @cached_property
    def sparse(self):
        import scipy.sparse as sp

        return sp.load_npz(IDX / "sparse.npz").tocsc()

    def bm25_query_tokens(self, query: str) -> list[str]:
        """Query tokens plus every alias of every identifier in the query (whole identifiers only)."""
        toks = tokenize(query)
        for m in TOKEN.finditer(query):
            t = m.group(0)
            if is_identifier(t):
                toks += [a.lower() for a in sorted(self.c.alias_names(t))]
        return toks

    def _finish(self, ranked: Ranked, depth: int) -> Ranked:
        r = self.cfg["retrieval"]
        return collapse(ranked, self.c, depth) if r.get("collapse_classes") else ranked[:depth]

    def _raw(self, depth: int) -> int:
        r = self.cfg["retrieval"]
        return max(depth, r.get("raw_depth", depth)) if r.get("collapse_classes") else depth

    def search_bm25(self, query: str, depth: int) -> Ranked:
        s = self.bm25.get_scores(self.bm25_query_tokens(query))
        return self._finish(_top(self.c.doc_ids, s, self._raw(depth)), depth)

    def search_dense(self, qvec: np.ndarray, depth: int) -> Ranked:
        scores, idx = self.dense_index.search(qvec.reshape(1, -1).astype(np.float32), self._raw(depth))
        return self._finish([(self.c.doc_ids[i], float(s)) for i, s in zip(idx[0], scores[0]) if i >= 0], depth)

    def search_sparse(self, qweights: dict[int, float], depth: int) -> Ranked:
        if not qweights:
            return []
        cols = np.fromiter(qweights.keys(), dtype=np.int64)
        w = np.fromiter(qweights.values(), dtype=np.float32)
        s = np.asarray(self.sparse[:, cols] @ w).ravel()
        return self._finish(_top(self.c.doc_ids, s, self._raw(depth)), depth)


def collapse(ranked: Ranked, corpus, depth: int) -> Ranked:
    """Keep the best-ranked member of every VU equivalence class (sections pass through) until
    `depth` distinct entries are collected (decision 2026-11-08: identical VU texts of ~40 drawing
    commands otherwise fill the whole top-50)."""
    out, seen = [], set()
    ck = class_key(corpus)
    for d, s in ranked:
        key = ck(d)
        if key in seen:
            continue
        seen.add(key)
        out.append((d, s))
        if len(out) == depth:
            break
    return out


def _top(ids: list[str], scores: np.ndarray, depth: int) -> Ranked:
    k = min(depth, len(scores))
    idx = np.argpartition(-scores, k - 1)[:k]
    idx = idx[np.lexsort((idx, -scores[idx]))]  # score desc, then doc order (deterministic ties)
    return [(ids[i], float(scores[i])) for i in idx if scores[i] > 0]


def rrf(lists: list[Ranked], k_rrf: int, depth: int, key=None) -> Ranked:
    """Reciprocal rank fusion. With `key` (chunk_id -> fusion key, e.g. the equivalence class) the
    votes of different members of one key are summed and the best-ranked member represents it."""
    key = key or (lambda d: d)
    score: dict[str, float] = {}
    first: dict[str, tuple[int, int]] = {}
    rep: dict[str, str] = {}
    for li, lst in enumerate(lists):
        for rank, (d, _) in enumerate(lst, 1):
            k = key(d)
            score[k] = score.get(k, 0.0) + 1.0 / (k_rrf + rank)
            if k not in first or (rank, li) < first[k]:
                first[k] = (rank, li)
                rep[k] = d
    order = sorted(score, key=lambda k: (-score[k], first[k], k))
    return [(rep[k], score[k]) for k in order[:depth]]


def class_key(corpus) -> callable:
    def key(d: str) -> str:
        c = corpus.chunks[d]
        return c["equiv_class_id"] if c["type"] == "vu" else d

    return key


class Reranker:
    def __init__(self, corpus: Corpus) -> None:
        self.c = corpus
        self.cache: dict[tuple[str, str], float] = {}

    @cached_property
    def model(self):
        from FlagEmbedding import FlagReranker

        from vkrag.index.embed import snapshot

        cfg = load_config()["reranker"]
        return FlagReranker(snapshot(cfg["model"], cfg.get("revision")), use_fp16=cfg.get("fp16", True), devices=["cuda:0"])

    def rerank(self, query: str, cands: Ranked, depth: int) -> Ranked:
        cfg = load_config()["reranker"]
        todo = [d for d, _ in cands if (query, d) not in self.cache]
        if todo:
            scores = self.model.compute_score([[query, self.c.text(d)] for d in todo], max_length=cfg["max_length"], batch_size=16)
            scores = scores if isinstance(scores, list) else [scores]
            for d, s in zip(todo, scores):
                self.cache[(query, d)] = float(s)
        order = sorted(((d, self.cache[(query, d)]) for d, _ in cands), key=lambda x: -x[1])
        return order[:depth]


def assemble_context(ranked: Ranked, corpus: Corpus, k: int) -> list[str]:
    """Top-k after dedup by chunk_id, by equivalence class (VU chunks) and by identical text."""
    out, seen_cls, seen_txt = [], set(), set()
    for d, _ in ranked:
        c = corpus.chunks[d]
        cls = c.get("equiv_class_id") if c["type"] == "vu" else None
        body = c["llm_text"].split("\n", 1)[-1].strip() if c["type"] == "vu" else c["llm_text"].strip()
        if d in out or (cls and cls in seen_cls) or body in seen_txt:
            continue
        out.append(d)
        if cls:
            seen_cls.add(cls)
        seen_txt.add(body)
        if len(out) == k:
            break
    return out


def oracle_context(q: dict, corpus: Corpus) -> list[str]:
    vu = corpus.chunks[q["vuid"]]
    sec = corpus.sections.get(vu["section_id"], [])
    return [q["vuid"]] + sec[:1]


def oracle_distract_context(q: dict, corpus: Corpus, dense: np.ndarray | None, seed: int, n: int = 4) -> tuple[list[str], int]:
    """Gold (as in oracle) + n distractor VU chunks outside the gold class and acceptable classes
    (PLAN §9.3): same entity, same entity-family prefix, same parent spec section, nearest by dense."""
    gold = corpus.chunks[q["vuid"]]
    banned_cls = {gold["equiv_class_id"]} | {
        corpus.chunks[a]["equiv_class_id"] for a in q.get("acceptable_vuids", []) if a in corpus.chunks
    }
    vus = [c for c in corpus.chunks.values() if c["type"] == "vu" and c["equiv_class_id"] not in banned_cls]
    fam = _family(gold["entity"])
    gsec = corpus.chunks[corpus.sections[gold["section_id"]][0]]["path"] if gold["section_id"] in corpus.sections else None
    levels = [
        [c for c in vus if c["entity"] == gold["entity"]],
        [c for c in vus if c["entity"] != gold["entity"] and _family(c["entity"]) == fam],
        [
            c
            for c in vus
            if gsec and corpus.sections.get(c["section_id"]) and corpus.chunks[corpus.sections[c["section_id"]][0]]["path"][:2] == gsec[:2]
        ],
    ]
    rng = random.Random(f"{seed}|{q['qid']}")
    picked, used_cls, level = [], set(), 0
    for li, pool in enumerate(levels, 1):
        pool = sorted(pool, key=lambda c: c["chunk_id"])
        rng.shuffle(pool)
        for c in pool:
            if len(picked) == n:
                break
            if c["equiv_class_id"] in used_cls:
                continue
            picked.append(c["chunk_id"])
            used_cls.add(c["equiv_class_id"])
            level = li
    if len(picked) < n and dense is not None:
        g = dense[corpus.row[q["vuid"]]]
        rows = [corpus.row[c["chunk_id"]] for c in vus]
        sims = dense[rows] @ g
        for r in np.argsort(-sims):
            c = vus[int(r)]
            if len(picked) == n:
                break
            if c["chunk_id"] in picked or c["equiv_class_id"] in used_cls:
                continue
            picked.append(c["chunk_id"])
            used_cls.add(c["equiv_class_id"])
            level = 4
    ctx = picked[:]
    pos = rng.randrange(len(ctx) + 1)
    gold_ctx = oracle_context(q, corpus)
    ctx[pos:pos] = gold_ctx[:1]
    ctx += gold_ctx[1:]  # the parent section part goes last, after the shuffled VU block
    return ctx, level


def _family(entity: str | None) -> str:
    """Command-family prefix: vkCmdDrawIndexedIndirect -> vkCmdDraw, VkImageCreateInfo -> VkImage."""
    if not entity:
        return ""
    words = [w for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", entity)]
    n = 3 if entity.startswith("vkCmd") else 2
    return "".join(words[:n])
