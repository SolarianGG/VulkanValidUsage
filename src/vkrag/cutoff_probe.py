"""`recent_cutoff_date` probe by extensions (PLAN §9.1).

1. select: date every extension by the first Vulkan-Docs tag whose vk.xml contains it (supported
   for `vulkan`); for each month from `start_month` to the month before the freeze take the
   extensions first published that month (all of them, or up to `per_month`, seeded). Only
   extensions with a `Description` section in the spec appendix are used: it is the judge's reference.
2. ask: closed-book "What does `VK_X_y` provide?" to each answerer (qwen via Ollama, remote via OpenRouter).
3. judge: the judge model decides `recognized` (the answer states the extension's actual purpose
   with at least one specific fact that cannot be guessed from the name alone).
4. months are grouped into bins (`bin: quarter`); cutoff = end of the last bin with recognized
   share >= 50% such that the next two bins are < 50% (decision 2026-11-07, PLAN §10).

Outputs in data/processed/cutoff_probe/: items.json, answers.jsonl, judged.jsonl, result.json.
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import date

from tqdm import tqdm

from vkrag.config import PROCESSED, load_config
from vkrag.history import docs_tag_dates, tag_key
from vkrag.ingest.registry import _xml_at

OUT = PROCESSED / "cutoff_probe"
QUESTION = ("What does the Vulkan extension {ext} provide? Answer in 2-3 sentences. "
            "If you do not know this extension, answer \"I don't know\".")
SYSTEM = "You are an expert on the Vulkan API. Answer concisely."
JUDGE_SYSTEM = (
    "You check whether a model knows a Vulkan extension. You get the extension name, the official description "
    "from the Vulkan specification and the model's answer. recognized=true only if the answer correctly states "
    "the extension's actual purpose and includes at least one specific fact consistent with the description that "
    "cannot be guessed from the extension name alone. A refusal, a generic guess from the name, or a description "
    "of a different feature is recognized=false. Reply with JSON only.")
JUDGE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {"name": "recognition", "strict": True, "schema": {
        "type": "object",
        "properties": {"recognized": {"type": "boolean"}, "reason": {"type": "string"}},
        "required": ["recognized", "reason"], "additionalProperties": False}},
}


def month_add(ym: str, k: int) -> str:
    y, m = map(int, ym.split("-"))
    m0 = y * 12 + m - 1 + k
    return f"{m0 // 12:04d}-{m0 % 12 + 1:02d}"


def extension_first_tags(start_month: str) -> tuple[dict[str, str], dict[str, str], str]:
    """Extension -> first tag (within tags from `start_month`), tag dates, baseline tag."""
    dates = docs_tag_dates()
    current = load_config()["spec"]["tag"]
    tags = sorted((t for t in dates if tag_key(t) <= tag_key(current)), key=tag_key)
    inside = [t for t in tags if dates[t][:7] >= start_month]
    baseline = [t for t in tags if dates[t][:7] < start_month][-1]
    first: dict[str, str] = {}
    for t in tqdm([baseline] + inside, desc="vk.xml"):
        root = _xml_at(t)
        for x in root.iter("extension"):
            sup = (x.get("supported") or "").split(",")
            if "vulkan" in sup and x.get("name") not in first:
                first[x.get("name")] = t
    return {k: v for k, v in first.items() if v != baseline}, dates, baseline


def descriptions() -> dict[str, str]:
    out = {}
    for line in open(PROCESSED / "chunks.jsonl", encoding="utf-8"):
        c = json.loads(line)
        p = c.get("path") or []
        if c["type"] == "section" and len(p) >= 3 and p[1] == "List of Current Extensions" and c["title"] == "Description":
            text = c["llm_text"].split("\n", 1)[1] if "\n" in c["llm_text"] else c["llm_text"]
            out[p[2]] = out.get(p[2], "") + text
    return out


def select() -> dict:
    cfg = load_config()
    pc = cfg["cutoff_probe"]
    freeze = date.fromisoformat(cfg["spec"]["freeze_date"])
    last = month_add(freeze.strftime("%Y-%m"), -1)
    months, m = [], pc["start_month"]
    while m <= last:
        months.append(m)
        m = month_add(m, 1)
    first, dates, baseline = extension_first_tags(months[0])
    reg = json.loads((PROCESSED / "registry.json").read_text(encoding="utf-8"))["extensions"]
    desc = descriptions()
    by_month = defaultdict(list)
    for ext, t in first.items():
        by_month[dates[t][:7]].append(ext)
    items, per_month = [], {}
    for m in months:
        pool = sorted(x for x in by_month.get(m, []) if x in desc and not reg.get(x, {}).get("provisional"))
        rng = random.Random(f"{cfg['seed']}-{m}")
        rng.shuffle(pool)
        pick = sorted(pool if pc.get("per_month") is None else pool[: pc["per_month"]])
        per_month[m] = {"published": len(by_month.get(m, [])), "eligible": len(pool), "picked": len(pick)}
        items += [{"month": m, "extension": x, "first_tag": first[x], "description": desc[x]} for x in pick]
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"months": months, "baseline_tag": baseline, "per_month": per_month, "items": items}
    (OUT / "items.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def _done(path, key_fields) -> set:
    if not path.exists():
        return set()
    out = set()
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue  # truncated last line
        out.add(tuple(r[k] for k in key_fields))
    return out


def _append(path, rec) -> None:
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()


def ask(models: list[str]) -> None:
    from vkrag.generation.ollama_client import Ollama
    from vkrag.generation.openrouter import OpenRouter, role

    cfg = load_config()
    items = json.loads((OUT / "items.json").read_text(encoding="utf-8"))["items"]
    path = OUT / "answers.jsonl"
    done = _done(path, ("model", "extension"))
    n_pred = cfg["cutoff_probe"]["max_tokens"]
    for m in models:
        if m == "qwen":
            cl = Ollama()
            digest = cl.digest()
        else:
            cl, rc = OpenRouter(), dict(role("answerer_remote"))
            order = cfg["cutoff_probe"].get("remote_provider")
            if order:
                rc["provider"] = dict(rc["provider"], order=[order])
        for it in tqdm(items, desc=m):
            if (m, it["extension"]) in done:
                continue
            msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": QUESTION.format(ext=it["extension"])}]
            if m == "qwen":
                r = cl.chat(msgs, num_predict=n_pred)
                rec = {"model": m, "model_id": cfg["ollama"]["model"], "digest": digest, "content": r.content,
                       "finish_reason": r.done_reason, "latency_s": r.latency_s}
            else:
                r = cl.chat(rc, msgs, max_tokens=n_pred)
                rec = {"model": m, "model_id": r.model, "provider": r.provider, "content": r.content,
                       "finish_reason": r.finish_reason, "cost_usd": r.cost_usd, "latency_s": r.latency_s}
            rec.update(extension=it["extension"], month=it["month"])
            _append(path, rec)
        if m == "qwen":
            cl.unload()


def judge() -> None:
    from vkrag.generation.openrouter import OpenRouter, role

    items = {i["extension"]: i for i in json.loads((OUT / "items.json").read_text(encoding="utf-8"))["items"]}
    answers = [json.loads(line) for line in open(OUT / "answers.jsonl", encoding="utf-8")]
    path = OUT / "judged.jsonl"
    done = _done(path, ("model", "extension"))
    o, rc = OpenRouter(), role("judge")
    order = load_config()["cutoff_probe"].get("judge_provider")
    if order:
        rc = dict(rc, provider=dict(rc["provider"], order=[order]))
    for a in tqdm(answers, desc="judge"):
        if (a["model"], a["extension"]) in done:
            continue
        it = items[a["extension"]]
        user = (f"Extension: {a['extension']}\n\nOfficial description:\n{it['description']}\n\n"
                f"Model answer:\n{a['content']}\n\nReturn recognized and a reason of at most 40 words.")
        for attempt in range(3):
            r = o.chat(rc, [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
                       response_format=JUDGE_SCHEMA)
            try:
                v = json.loads(r.content or "")
                break
            except json.JSONDecodeError:
                v = None
        rec = {"model": a["model"], "extension": a["extension"], "month": a["month"],
               "recognized": None if v is None else v["recognized"], "reason": None if v is None else v["reason"],
               "judge_model": r.model, "judge_provider": r.provider, "cost_usd": r.cost_usd,
               "reasoning_tokens": r.reasoning_tokens}
        _append(path, rec)


def bin_of(month: str, how: str) -> str:
    if how == "month":
        return month
    y, m = month.split("-")
    return f"{y}-Q{(int(m) - 1) // 3 + 1}"


def bin_end(b: str) -> str:
    """Last day of a bin (`YYYY-MM` or `YYYY-Qn`)."""
    import calendar

    y, rest = b.split("-")
    m = int(rest[1:]) * 3 if rest.startswith("Q") else int(rest)
    return f"{y}-{m:02d}-{calendar.monthrange(int(y), m)[1]:02d}"


def cutoff_month(share: dict[str, float | None], months: list[str], thr: float = 0.5) -> str | None:
    """Last bin with share >= thr such that the next two bins (with data) are < thr."""
    ms = [m for m in months if share.get(m) is not None]
    best = None
    for i, m in enumerate(ms):
        nxt = ms[i + 1 : i + 3]
        if share[m] >= thr and len(nxt) == 2 and all(share[x] < thr for x in nxt):
            best = m
    return best


def result() -> dict:
    data = json.loads((OUT / "items.json").read_text(encoding="utf-8"))
    how = load_config()["cutoff_probe"].get("bin", "quarter")
    wanted = {i["extension"] for i in data["items"]}
    judged = [j for j in (json.loads(line) for line in open(OUT / "judged.jsonl", encoding="utf-8")) if j["extension"] in wanted]
    bins = sorted({bin_of(m, how) for m in data["months"]})
    out = {"months": data["months"], "bin": how, "bins": bins, "models": {}}
    for model in sorted({j["model"] for j in judged}):
        by_m = defaultdict(lambda: [0, 0])
        by_b = defaultdict(lambda: [0, 0])
        for j in judged:
            if j["model"] == model and j["recognized"] is not None:
                for d, k in ((by_m, j["month"]), (by_b, bin_of(j["month"], how))):
                    d[k][0] += j["recognized"]
                    d[k][1] += 1
        share = {b: (by_b[b][0] / by_b[b][1] if by_b[b][1] else None) for b in bins}
        cut = cutoff_month(share, bins)
        out["models"][model] = {
            "by_month": {mo: {"recognized": by_m[mo][0], "n": by_m[mo][1]} for mo in data["months"]},
            "by_bin": {b: {"recognized": by_b[b][0], "n": by_b[b][1], "share": None if share[b] is None else round(share[b], 3)} for b in bins},
            "cutoff_bin": cut, "cutoff_date": bin_end(cut) if cut else None,
        }
    out["judge_cost_usd"] = round(sum(j.get("cost_usd") or 0 for j in judged), 4)
    (OUT / "result.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out
