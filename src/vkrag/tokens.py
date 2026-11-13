"""Token counting with the three tokenizers that bound chunk length (PLAN Stage 1, item 13).

- qwen: the local answerer (qwen3.5);
- xlmr: bge-m3 / bge-reranker-v2-m3 (XLM-R vocabulary; query + chunk must fit max_length=1024);
- remote: the OpenRouter answerer (DeepSeek V4 Flash).

Only `tokenizer.json` is downloaded; the resolved commit of each repo is returned for the manifest.
"""

from __future__ import annotations

from functools import cache

from huggingface_hub import HfApi, hf_hub_download
from tokenizers import Tokenizer

TOKENIZER_REPOS = {
    "qwen": "Qwen/Qwen3.5-9B",
    "xlmr": "BAAI/bge-m3",
    "remote": "deepseek-ai/DeepSeek-V4-Flash-0731",
}


@cache
def _resolve(repo: str) -> str:
    return HfApi().model_info(repo).sha


@cache
def get(name: str) -> Tokenizer:
    repo = TOKENIZER_REPOS[name]
    path = hf_hub_download(repo, "tokenizer.json", revision=_resolve(repo))
    return Tokenizer.from_file(path)


def revisions() -> dict[str, str]:
    return {name: f"{repo}@{_resolve(repo)}" for name, repo in TOKENIZER_REPOS.items()}


def count(text: str, name: str) -> int:
    return len(get(name).encode(text, add_special_tokens=False).ids)


def count_max(text: str) -> int:
    """Maximum token count over all three tokenizers."""
    return max(count(text, n) for n in TOKENIZER_REPOS)


def count_all(text: str) -> dict[str, int]:
    return {n: count(text, n) for n in TOKENIZER_REPOS}
