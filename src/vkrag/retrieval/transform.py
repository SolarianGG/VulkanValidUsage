"""Phase A (PLAN §4 Stage 5): query rewrite and HyDE by the local qwen -> runs/<run_id>/query_transforms.jsonl.

Only Ollama uses the GPU in this phase; the model is unloaded at the end (keep_alive=0). Every record
carries the prompt hash and the model digest (cache key) and the identifiers in the output that do
not exist in identifiers.json / aliases.json / the SPIR-V dictionary (transform hallucinations).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from vkrag.config import ROOT, load_config
from vkrag.generation.ollama_client import Ollama
from vkrag.index.tokenize import TOKEN, is_identifier

PROMPTS = Path(__file__).resolve().parents[1] / "generation" / "prompts"
KINDS = ("rewrite", "hyde")


def prompt(kind: str) -> tuple[str, str]:
    text = (PROMPTS / f"{kind}.md").read_text(encoding="utf-8").strip()
    return text, hashlib.sha256(text.encode()).hexdigest()[:12]


def clean(kind: str, text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    if kind == "rewrite":
        line = next((l for l in text.splitlines() if l.strip()), "")
        return line.strip().strip('"').strip("`").strip()
    return text


def unknown_identifiers(text: str, lex) -> list[str]:
    out = []
    for m in TOKEN.finditer(text):
        t = m.group(0)
        if is_identifier(t) and t.startswith(("vk", "Vk", "VK_")) and not lex.exists(t):
            out.append(t)
    return sorted(set(out))


def load(run_id: str) -> dict[tuple[str, str], dict]:
    p = ROOT / "runs" / run_id / "query_transforms.jsonl"
    out = {}
    if p.exists():
        for line in open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            out[(r["qid"], r["kind"])] = r
    return out


def run(sample: str, run_id: str) -> dict:
    from vkrag.questions.validate import Lexicon
    from vkrag.retrieval.run import load_questions

    cfg = load_config()
    oc = cfg["ollama"]
    cli = Ollama()
    digest = cli.digest()
    lex = Lexicon()
    rdir = ROOT / "runs" / run_id
    rdir.mkdir(parents=True, exist_ok=True)
    have = load(run_id)
    prompts = {k: prompt(k) for k in KINDS}
    stats = {"written": 0, "unknown_identifier_share": {}, "truncated": 0}
    with open(rdir / "query_transforms.jsonl", "a", encoding="utf-8") as f:
        for q in load_questions(sample):
            for kind in KINDS:
                text, ph = prompts[kind]
                old = have.get((q["qid"], kind))
                if old and old["prompt_hash"] == ph and old["model_digest"] == digest and old["question_hash"] == q["question_hash"]:
                    continue
                res = cli.chat(
                    [{"role": "system", "content": text}, {"role": "user", "content": q["question"]}], num_predict=oc["num_predict"][kind]
                )
                out = clean(kind, res.content)
                rec = {
                    "qid": q["qid"],
                    "kind": kind,
                    "question_hash": q["question_hash"],
                    "prompt_hash": ph,
                    "model": oc["model"],
                    "model_digest": digest,
                    "text": out,
                    "done_reason": res.done_reason,
                    "prompt_tokens": res.prompt_eval_count,
                    "completion_tokens": res.eval_count,
                    "latency_s": res.latency_s,
                    "unknown_identifiers": unknown_identifiers(out, lex),
                }
                stats["truncated"] += res.done_reason == "length"
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                stats["written"] += 1
    cli.unload()
    time.sleep(3)
    allr = load(run_id)
    for kind in KINDS:
        rs = [r for (qid, k), r in allr.items() if k == kind]
        stats["unknown_identifier_share"][kind] = round(sum(bool(r["unknown_identifiers"]) for r in rs) / max(len(rs), 1), 3)
    return stats
