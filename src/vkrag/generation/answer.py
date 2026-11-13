"""Phase C (PLAN §4 Stage 6): answers of the local qwen and the remote answerer -> runs/<run_id>/answers.jsonl.

Contexts come from phase B (`retrieved.jsonl`, current config hash and question hash only). Every call
is logged in `runs/<run_id>/usage.jsonl` (failed attempts included). Records are cached by a key over
(qid, question_hash, config, answerer, repeat_idx, retrieval_hash, prompt_hash, model identity,
generation parameters); a rerun only fills what is missing or stale.

Skip policy (PLAN Stage 6): an error is retried up to 3 times with backoff; a truncated or empty answer
is retried once with a doubled output limit; after that the answer is recorded with `missing=true`.
For qwen the prompt is counted locally with the Qwen chat template (thinking off) and
`prompt_tokens + num_predict <= num_ctx` is checked before the call.
"""

from __future__ import annotations

import hashlib
import json
import time
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

from vkrag.config import PROCESSED, ROOT, load_config

PROMPTS = Path(__file__).resolve().parent / "prompts"
GEN_CONFIGS = ("closed", "oracle", "oracle_distract", "bm25", "dense", "rrf", "rrf_rerank", "rewrite_rrf_rerank", "hyde_rrf_rerank")
# exploratory controls: strict prompt over the rrf_rerank context; k in {3, 10} for rrf_rerank (pilot, H5 trade-off)
CONTROL_CONFIGS = ("rrf_rerank_strict", "rrf_rerank_k3", "rrf_rerank_k10")
ANSWERERS = ("qwen", "remote")
QWEN_TOKENIZER = ("Qwen/Qwen3.5-9B", "c202236235762e1c871ad0ccb60c8ee5ba337b9a")
YES_NO_SUFFIX = "Start your answer with Yes or No."
REMOTE_OUTPUT_TOKENS_EST = 200


def _h(obj) -> str:
    s = obj if isinstance(obj, str) else json.dumps(obj, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def prompt_kind(config: str) -> str:
    if config == "closed":
        return "closed"
    return "strict" if config.endswith("_strict") else "rag"


def system_prompt(kind: str) -> tuple[str, str]:
    t = (PROMPTS / f"answer_{kind}.md").read_text(encoding="utf-8").strip()
    return t, _h(t)[:12]


def source_config(config: str) -> tuple[str | None, int | None]:
    """Phase-B configuration whose context is used, and a k override (None = the stored context)."""
    if config == "closed":
        return None, None
    if config.endswith("_strict"):
        return config.removesuffix("_strict"), None
    if "_k" in config and config.rsplit("_k", 1)[1].isdigit():
        base, k = config.rsplit("_k", 1)
        return base, int(k)
    return config, None


def render_context(ids: list[str], chunks: dict[str, dict]) -> str:
    """PLAN §9.3: `[n] (VU | Section: <title>)` + llm_text, items separated by `\\n---\\n`."""
    items = []
    for n, cid in enumerate(ids, 1):
        c = chunks[cid]
        label = "VU" if c["type"] == "vu" else f"Section: {c['title']}"
        items.append(f"[{n}] ({label})\n{c['llm_text'].strip()}")
    return "\n---\n".join(items)


def user_message(q: dict, ctx_ids: list[str] | None, chunks: dict[str, dict]) -> str:
    question = q["question"].strip()
    if q.get("answer_type") == "yes_no":
        question += "\n" + YES_NO_SUFFIX
    if ctx_ids is None:
        return question
    return f"Context:\n{render_context(ctx_ids, chunks)}\n\nQuestion: {question}"


@lru_cache(maxsize=1)
def qwen_tokenizer():
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(QWEN_TOKENIZER[0], revision=QWEN_TOKENIZER[1])


def qwen_prompt_tokens(messages: list[dict]) -> int:
    """Prompt length with the Qwen3.5 chat template, thinking off (the template Ollama renders)."""
    tok = qwen_tokenizer()
    s = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return len(tok(s, add_special_tokens=False).input_ids)


# ---------------------------------------------------------------- inputs


def load_chunks() -> dict[str, dict]:
    out = {}
    for line in open(PROCESSED / "chunks.jsonl", encoding="utf-8"):
        c = json.loads(line)
        out[c["chunk_id"]] = {k: c.get(k) for k in ("chunk_id", "type", "title", "llm_text", "equiv_class_id")}
    return out


def load_contexts(run_id: str, configs: tuple[str, ...], qs: list[dict], chunks: dict) -> dict[tuple[str, str], list[str]]:
    """(qid, config) -> context chunk ids from the current phase-B records."""
    from vkrag.retrieval.core import assemble_context
    from vkrag.retrieval.run import config_hash

    cfg = load_config()
    need = {source_config(c)[0] for c in configs} - {None}
    hashes = {c: config_hash(c, cfg) for c in need}
    qh = {q["qid"]: q["question_hash"] for q in qs}
    stored: dict[tuple[str, str], dict] = {}
    for line in open(ROOT / "runs" / run_id / "retrieved.jsonl", encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r["config"] in hashes and r["config_hash"] == hashes[r["config"]] and qh.get(r["qid"]) == r["question_hash"]:
            stored[(r["qid"], r["config"])] = r
    corpus = SimpleNamespace(chunks=chunks)
    out = {}
    for c in configs:
        src, k = source_config(c)
        if src is None:
            continue
        for q in qs:
            r = stored.get((q["qid"], src))
            if r is None:
                if src.startswith("oracle") and q["stratum"] == "unanswerable":
                    continue
                raise RuntimeError(f"no current phase-B record for ({q['qid']}, {src}); run `vkrag retrieve`")
            out[(q["qid"], c)] = assemble_context([(d, s) for d, s in r["ranked"]], corpus, k) if k else r["context"]
    return out


def gen_questions(sample: str) -> list[dict]:
    from vkrag.retrieval.run import load_questions

    return [q for q in load_questions(sample) if q.get("in_generation")]


def jobs(
    sample: str, run_id: str, configs: tuple[str, ...], answerers: tuple[str, ...], repeat_idx: int = 0, limit: int | None = None
) -> tuple[list[dict], dict]:
    qs = gen_questions(sample)
    if limit:
        qs = qs[:limit]
    chunks = load_chunks()
    ctx = load_contexts(run_id, configs, qs, chunks)
    out = []
    for a in answerers:
        for q in qs:
            for c in configs:
                if c != "closed" and (q["qid"], c) not in ctx:
                    continue  # oracle* for unanswerable
                ids = ctx.get((q["qid"], c))
                system, ph = system_prompt(prompt_kind(c))
                out.append(
                    {
                        "qid": q["qid"],
                        "config": c,
                        "answerer": a,
                        "repeat_idx": repeat_idx,
                        "question_hash": q["question_hash"],
                        "context": ids,
                        "retrieval_hash": _h(ids) if ids is not None else None,
                        "prompt_hash": ph,
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_message(q, ids, chunks)}],
                    }
                )
    return out, chunks


# ---------------------------------------------------------------- answerers


def model_identity(answerer: str, cfg: dict) -> dict:
    if answerer == "qwen":
        o = cfg["ollama"]
        return {
            "model_id": o["model"],
            "model_digest": o["digest"],
            "params": {k: o[k] for k in ("num_ctx", "temperature", "presence_penalty", "think")}
            | {"num_predict": o["num_predict"]["answer"]},
        }
    rc = cfg["openrouter"]["answerer_remote"]
    return {
        "model_id": rc["model"],
        "provider": rc["provider"],
        "params": {"reasoning": rc.get("reasoning"), "max_tokens": rc["max_tokens"], "temperature": rc.get("temperature", 0)},
    }


def cache_key(job: dict, ident: dict) -> str:
    keys = ("qid", "question_hash", "config", "answerer", "repeat_idx", "retrieval_hash", "prompt_hash")
    return _h({k: job[k] for k in keys} | {"model": ident})


def _done(path: Path) -> dict[str, dict]:
    out = {}
    if path.exists():
        for line in open(path, encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue  # a truncated last line is dropped
            out[r["key"]] = r
    return out


class QwenAnswerer:
    name = "qwen"

    def __init__(self, cfg: dict):
        from vkrag.generation.ollama_client import Ollama

        self.cfg = cfg["ollama"]
        self.cli = Ollama(self.cfg)
        digest = self.cli.digest()
        if (digest or "").removeprefix("sha256:") != self.cfg["digest"].removeprefix("sha256:"):
            raise RuntimeError(f"Ollama model digest {digest} != config {self.cfg['digest']}")

    def call(self, messages: list[dict], limit: int) -> dict:
        n_prompt = qwen_prompt_tokens(messages)
        num_ctx = self.cfg["num_ctx"]
        if n_prompt + limit > num_ctx:
            limit = num_ctx - n_prompt
            if limit < 64:
                raise ContextOverflow(f"prompt {n_prompt} tokens leaves {limit} of num_ctx {num_ctx}")
        r = self.cli.chat(messages, num_predict=limit)
        return {
            "content": r.content,
            "finish_reason": r.done_reason,
            "prompt_tokens_local": n_prompt,
            "prompt_tokens": r.prompt_eval_count,
            "completion_tokens": r.eval_count,
            "reasoning_tokens": 0,
            "latency_s": r.latency_s,
            "actual_model": r.model,
            "provider": "ollama",
            "cost_usd": None,
            "cached_tokens": None,
            "num_predict": limit,
        }

    def default_limit(self) -> int:
        return self.cfg["num_predict"]["answer"]

    def close(self) -> None:
        self.cli.unload()

    def gpu_share(self) -> float | None:
        ps = self.cli.http.get("/api/ps").json().get("models", [])
        m = next((m for m in ps if m["name"].split(":")[0] == self.cfg["model"].split(":")[0]), None)
        return round(m["size_vram"] / m["size"], 3) if m and m.get("size") else None


class RemoteAnswerer:
    name = "remote"

    def __init__(self, cfg: dict):
        from vkrag.generation.openrouter import OpenRouter

        self.rc = cfg["openrouter"]["answerer_remote"]
        if not self.rc["provider"].get("order"):
            raise RuntimeError("openrouter.answerer_remote.provider.order must pin one provider")
        self.cli = OpenRouter(retries=0)  # retries are counted by the skip policy here

    def call(self, messages: list[dict], limit: int) -> dict:
        r = self.cli.chat(self.rc, messages, max_tokens=limit)
        family = self.rc["model"].rsplit("-", 1)[0]  # deepseek/deepseek-v4-flash
        if not (r.model or "").startswith(family):
            raise ModelMismatch(f"model {r.model} != {self.rc['model']}")
        want = self.rc["provider"]["order"][0].split("/")[0].lower()
        if (r.provider or "").lower().replace(" ", "") != want:
            raise ModelMismatch(f"provider {r.provider} != {want}")
        return {
            "content": r.content,
            "finish_reason": r.finish_reason,
            "prompt_tokens_local": None,
            "prompt_tokens": r.usage.get("prompt_tokens"),
            "completion_tokens": r.usage.get("completion_tokens"),
            "reasoning_tokens": r.reasoning_tokens,
            "latency_s": r.latency_s,
            "actual_model": r.model,
            "provider": r.provider,
            "cost_usd": r.cost_usd,
            "cached_tokens": r.cached_tokens,
            "num_predict": limit,
            "has_reasoning_text": bool((r.reasoning or "").strip()),
        }

    def default_limit(self) -> int:
        return self.rc["max_tokens"]

    def close(self) -> None:
        pass


class ContextOverflow(RuntimeError):
    pass


class ModelMismatch(RuntimeError):
    pass


def answer_one(
    ans,
    job: dict,
    usage_f,
    run_id: str,
    max_errors: int = 3,
    backoff_s: float = 5.0,
    start_limit: int | None = None,
    max_limit: int | None = None,
) -> dict:
    """One answer under the skip policy; every attempt goes to usage.jsonl.
    `start_limit`/`max_limit` (re-runs of missing answers): start at `start_limit` and keep doubling on
    truncation while the doubled limit stays <= `max_limit` (default: one doubling)."""
    limit = start_limit or ans.default_limit()
    errors, truncations, last_error, res = 0, 0, None, None
    while True:
        attempt = errors + truncations
        try:
            res = ans.call(job["messages"], limit)
        except (ContextOverflow, ModelMismatch) as e:  # not retryable: a config problem
            last_error, res = f"{type(e).__name__}: {e}", None
            _usage(usage_f, job, ans.name, attempt, None, last_error)
            break
        except Exception as e:  # noqa: BLE001 - network / HTTP / Ollama errors are retried
            errors += 1
            last_error, res = f"{type(e).__name__}: {str(e)[:300]}", None
            _usage(usage_f, job, ans.name, attempt, None, last_error)
            if errors > max_errors:
                break
            time.sleep(backoff_s * 2 ** (errors - 1))
            continue
        content = (res["content"] or "").strip()
        truncated = res["finish_reason"] == "length" or not content
        _usage(usage_f, job, ans.name, attempt, res, "truncated" if truncated else None)
        if not truncated:
            break
        truncations += 1
        last_error = f"truncated (finish_reason={res['finish_reason']}, limit={limit})"
        if (truncations > 1) if max_limit is None else (limit * 2 > max_limit):
            break
        limit *= 2
    ok = res is not None and (res["content"] or "").strip() and res["finish_reason"] != "length"
    rec = {k: job[k] for k in ("qid", "config", "answerer", "repeat_idx", "question_hash", "context", "retrieval_hash", "prompt_hash")}
    rec.update(
        {
            "answer": (res["content"] or "").strip() if ok else None,
            "missing": not ok,
            "error": None if ok else last_error,
            "retries": errors + truncations,
        }
    )
    if res is not None:
        rec.update(
            {
                k: res.get(k)
                for k in (
                    "finish_reason",
                    "prompt_tokens_local",
                    "prompt_tokens",
                    "completion_tokens",
                    "reasoning_tokens",
                    "latency_s",
                    "actual_model",
                    "provider",
                    "cost_usd",
                    "cached_tokens",
                    "num_predict",
                )
            }
        )
    return rec


def _usage(f, job: dict, answerer: str, attempt: int, res: dict | None, error: str | None) -> None:
    row = {
        "ts": round(time.time(), 3),
        "phase": "C",
        "qid": job["qid"],
        "config": job["config"],
        "model": answerer,
        "repeat_idx": job["repeat_idx"],
        "attempt": attempt,
        "error": error,
    }
    if res:
        row.update(
            {
                k: res.get(k)
                for k in (
                    "prompt_tokens",
                    "prompt_tokens_local",
                    "completion_tokens",
                    "reasoning_tokens",
                    "latency_s",
                    "provider",
                    "finish_reason",
                    "cost_usd",
                    "cached_tokens",
                )
            }
        )
    f.write(json.dumps(row) + "\n")
    f.flush()


# ---------------------------------------------------------------- run


def remote_pricing(cfg: dict) -> dict:
    """Price of the pinned endpoint (providers differ from the model-level price)."""
    from vkrag.generation.openrouter import OpenRouter

    rc = cfg["openrouter"]["answerer_remote"]
    tag = rc["provider"]["order"][0]
    ep = next((e for e in OpenRouter().endpoints(rc["model"]) if e.get("tag") == tag), None)
    if ep is None:
        raise RuntimeError(f"endpoint {tag} of {rc['model']} is not listed")
    return ep["pricing"]


def estimate(todo: list[dict], cfg: dict) -> dict:
    """Calls per answerer, qwen prompt sizes, remote cost estimate (DeepSeek tokenizer + model price)."""
    from vkrag import tokens

    out: dict = {}
    for a in ANSWERERS:
        js = [j for j in todo if j["answerer"] == a]
        if not js:
            continue
        e = {"calls": len(js)}
        if a == "qwen":
            n = [qwen_prompt_tokens(j["messages"]) for j in js]
            lim = cfg["ollama"]["num_ctx"] - cfg["ollama"]["num_predict"]["answer"]
            e.update({"prompt_tokens_max": max(n), "prompt_tokens_mean": round(sum(n) / len(n)), "over_num_ctx": sum(x > lim for x in n)})
        else:
            price = remote_pricing(cfg)
            tin = sum(tokens.count(m["content"], "remote") + 8 for j in js for m in j["messages"])
            tout = REMOTE_OUTPUT_TOKENS_EST * len(js)
            e.update(
                {
                    "input_tokens": tin,
                    "output_tokens_est": tout,
                    "price": {k: price.get(k) for k in ("prompt", "completion")},
                    "est_usd": round(tin * float(price.get("prompt", 0)) + tout * float(price.get("completion", 0)), 4),
                }
            )
        out[a] = e
    return out


def run(
    sample: str,
    run_id: str,
    configs: tuple[str, ...] = GEN_CONFIGS,
    answerers: tuple[str, ...] = ANSWERERS,
    repeat_idx: int = 0,
    dry_run: bool = False,
    max_usd: float | None = None,
    limit: int | None = None,
    retry_missing: bool = False,
    start_limit: int | None = None,
    max_limit: int | None = None,
) -> dict:
    cfg = load_config()
    rdir = ROOT / "runs" / run_id
    out_file, usage_file = rdir / "answers.jsonl", rdir / "usage.jsonl"
    all_jobs, _ = jobs(sample, run_id, configs, answerers, repeat_idx, limit)
    idents = {a: model_identity(a, cfg) for a in answerers}
    done = _done(out_file)
    todo = []
    for j in all_jobs:
        j["key"] = cache_key(j, idents[j["answerer"]])
        old = done.get(j["key"])
        if old is None or (retry_missing and old["missing"]):
            todo.append(j)
    stats = {"jobs": len(all_jobs), "todo": len(todo), "estimate": estimate(todo, cfg) if todo else {}}
    if dry_run or not todo:
        return stats
    est = stats["estimate"].get("remote", {}).get("est_usd", 0)
    if max_usd is not None and est > max_usd:
        raise RuntimeError(f"estimated remote cost ${est:.2f} > limit ${max_usd:.2f}")
    _manifest(rdir, cfg, answerers, configs)
    spent, written, missing = 0.0, 0, 0
    with open(out_file, "a", encoding="utf-8") as f, open(usage_file, "a", encoding="utf-8") as uf:
        for a in answerers:
            js = [j for j in todo if j["answerer"] == a]
            if not js:
                continue
            ans = QwenAnswerer(cfg) if a == "qwen" else RemoteAnswerer(cfg)
            t0 = time.time()
            try:
                for i, j in enumerate(js):
                    rec = answer_one(ans, j, uf, run_id, start_limit=start_limit, max_limit=max_limit)
                    rec.update({"key": j["key"], "model_id": idents[a]["model_id"]})
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    written += 1
                    missing += rec["missing"]
                    spent += rec.get("cost_usd") or 0.0
                    if a == "qwen" and i == 0:
                        stats["qwen_gpu_share"] = ans.gpu_share()
                    if max_usd is not None and spent > max_usd:
                        stats["stopped_at_budget"] = written
                        return stats | {"written": written, "missing": missing, "spent_usd": round(spent, 4)}
            finally:
                ans.close()
            stats[f"{a}_seconds"] = round(time.time() - t0, 1)
    return stats | {"written": written, "missing": missing, "spent_usd": round(spent, 4)}


def _manifest(rdir: Path, cfg: dict, answerers: tuple[str, ...], configs: tuple[str, ...]) -> None:
    p = rdir / "manifest.json"
    man = json.load(open(p, encoding="utf-8")) if p.exists() else {}
    g = man.setdefault("generation", {})
    g["prompt_hashes"] = {k: system_prompt(k)[1] for k in ("closed", "rag", "strict")}
    g["configs"] = sorted(set(g.get("configs", [])) | set(configs))
    if "qwen" in answerers:
        import httpx

        ver = httpx.get(cfg["ollama"]["host"] + "/api/version", timeout=10).json().get("version")
        g["qwen"] = {"ollama_version": ver, "chat_template_tokenizer": "@".join(QWEN_TOKENIZER)} | model_identity("qwen", cfg)
    if "remote" in answerers:
        price = remote_pricing(cfg)
        g["remote"] = model_identity("remote", cfg) | {"pricing": price, "pricing_date": time.strftime("%Y-%m-%d")}
    p.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
