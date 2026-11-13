"""bge-m3 embedder (PLAN §2, §4 Stage 4): FlagEmbedding BGEM3FlagModel, fp16 on GPU, normalized
dense vectors and lexical (sparse) weights from the same pass, explicit max_length, pinned revision."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from vkrag.config import load_config


def snapshot(repo: str, revision: str | None) -> str:
    from huggingface_hub import snapshot_download

    return snapshot_download(repo, revision=revision, local_files_only=True)


@lru_cache(maxsize=1)
def model():
    from FlagEmbedding import BGEM3FlagModel

    cfg = load_config()["embedder"]
    return BGEM3FlagModel(
        snapshot(cfg["model"], cfg.get("revision")),
        use_fp16=cfg.get("fp16", True),
        devices="cuda:0",
        normalize_embeddings=True,
        passage_max_length=cfg["max_length"],
        query_max_length=cfg["max_length"],
    )


def encode_full(texts: list[str], sparse: bool = True, batch_size: int | None = None) -> dict:
    cfg = load_config()["embedder"]
    out = model().encode(
        texts,
        batch_size=batch_size or cfg["batch_size"],
        max_length=cfg["max_length"],
        return_dense=True,
        return_sparse=sparse,
        return_colbert_vecs=False,
    )
    res = {"dense": np.asarray(out["dense_vecs"], dtype=np.float32)}
    if sparse:
        res["sparse"] = [{int(k): float(v) for k, v in w.items()} for w in out["lexical_weights"]]
    return res


def encode(texts: list[str], batch_size: int | None = None) -> np.ndarray:
    return encode_full(texts, sparse=False, batch_size=batch_size)["dense"]


def revision() -> str | None:
    return load_config()["embedder"].get("revision")
