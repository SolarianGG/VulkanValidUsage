"""Stage 3a: generator inputs for Claude Code (PLAN §4 Stage 3, §9.3 "Question generation").

`prepare(sample)` writes, for the frozen main or pilot sample:
  data/questions/generation_log/<sample>_assignments.json
      per VU: qids of both styles, answer_type and expected_verdict (assigned by code), the style
      that goes to the expensive phases (gen_style), batch number
  data/questions/generation_log/batches/<sample>/batch_NNN.input.json
      items + a shared context pool (entities with their section parts and all VUs, ref sections)
  data/questions/generation_log/batches/<sample>/batch_unans.input.json
      unanswerable quotas, candidate entities and the identifier sources for the existence check

All assignments are deterministic functions of the config seed and the frozen sample.
"""
from __future__ import annotations

import hashlib
import json
import random
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from vkrag.config import DATA, EXTERNAL, PROCESSED, RAW, load_config

QDIR = DATA / "questions"
GLOG = QDIR / "generation_log"
STYLES = ("identifier", "descriptive")
ANSWER_TYPES = ("rule", "yes_no", "scenario")
PROMPT_VERSION = "prompt_v2"

MAX_ITEMS_PER_BATCH = 25
MAX_CONTEXT_CHARS = 240_000   # distinct shared context per batch (~60-70k tokens)
MAX_REFS_PER_ITEM = 6


def stable_seed(seed: int, *parts: str) -> int:
    h = hashlib.sha256("|".join([str(seed), *parts]).encode()).hexdigest()
    return int(h[:12], 16)


def qid_of(sample: str, vuid: str, style: str) -> str:
    return f"q{sample[0]}-" + hashlib.sha256(f"{vuid}|{style}".encode()).hexdigest()[:10] + ("-id" if style == "identifier" else "-de")


def quotas(n: int, mix: dict[str, float], rng: random.Random) -> dict[str, int]:
    """Largest-remainder apportionment of n over mix; ties broken by rng."""
    raw = {k: n * w for k, w in mix.items()}
    q = {k: int(v) for k, v in raw.items()}
    order = sorted(mix, key=lambda k: (-(raw[k] - q[k]), rng.random()))
    for k in order[: n - sum(q.values())]:
        q[k] += 1
    return q


def balanced_split(groups: dict[str, list[str]], labels: tuple[str, str], rng: random.Random) -> dict[str, str]:
    """Two labels 50/50 inside every group; the odd leftover of a group alternates between the labels
    across groups (in a seeded order), so the overall split is also as even as possible."""
    odd = [g for g in sorted(groups) if len(groups[g]) % 2]
    rng.shuffle(odd)
    extra = {g: labels[i % 2] for i, g in enumerate(odd)}
    out: dict[str, str] = {}
    for g in sorted(groups):
        vs = groups[g]
        lab = list(labels) * (len(vs) // 2) + ([extra[g]] if g in extra else [])
        rng.shuffle(lab)
        out.update(zip(vs, lab))
    return out


def assign(vuids: list[str], strata: dict[str, dict], cfg: dict, sample: str) -> dict[str, dict]:
    """answer_type (target mix per stratum), expected_verdict (50/50 inside the stratum among yes_no),
    gen_style (50/50 inside the stratum), qids."""
    seed = cfg["seed"]
    mix = cfg["questions"]["answer_type_mix"]
    by_stratum: dict[str, list[str]] = defaultdict(list)
    for v in sorted(vuids):
        by_stratum[strata[v]["stratum"]].append(v)
    out: dict[str, dict] = {}
    yn_by_stratum: dict[str, list[str]] = {}
    for st, vs in sorted(by_stratum.items()):
        rng = random.Random(stable_seed(seed, sample, "answer_type", st))
        q = quotas(len(vs), mix, rng)
        order = vs[:]
        rng.shuffle(order)
        types = [t for t in ANSWER_TYPES for _ in range(q[t])]
        for v, t in zip(order, types):
            out[v] = {"answer_type": t}
        yn_by_stratum[st] = [v for v in order if out[v]["answer_type"] == "yes_no"]
    verdict = balanced_split(yn_by_stratum, ("yes", "no"), random.Random(stable_seed(seed, sample, "verdict")))
    style = balanced_split({st: sorted(vs) for st, vs in by_stratum.items()}, STYLES,
                           random.Random(stable_seed(seed, sample, "gen_style")))
    for v in out:
        out[v]["gen_style"] = style[v]
        if v in verdict:
            out[v]["expected_verdict"] = verdict[v]
    for v, a in out.items():
        a["stratum"] = strata[v]["stratum"]
        a["qids"] = {s: qid_of(sample, v, s) for s in STYLES}
    return out


def vkxml_relations(path: Path) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Types used by members/params of each struct/command, and the structs extending each struct (pNext)."""
    root = ET.parse(path).getroot()
    uses: dict[str, set[str]] = defaultdict(set)
    extenders: dict[str, set[str]] = defaultdict(set)
    for t in root.iter("type"):
        name = t.get("name")
        if t.get("category") not in ("struct", "union") or not name:
            continue
        for m in t.findall("member"):
            if m.findtext("type"):
                uses[name].add(m.findtext("type"))
        for base in filter(None, (t.get("structextends") or "").split(",")):
            extenders[base].add(name)
    for c in root.iter("command"):
        name = c.findtext("proto/name")
        if not name:
            continue
        for p in c.findall("param"):
            if p.findtext("type"):
                uses[name].add(p.findtext("type"))
    return uses, extenders


class Corpus:
    def __init__(self) -> None:
        self.vus = [json.loads(l) for l in open(PROCESSED / "vuids.jsonl", encoding="utf-8")]
        self.vu = {v["vuid"]: v for v in self.vus}
        self.by_entity: dict[str, list[dict]] = defaultdict(list)
        for v in self.vus:
            self.by_entity[v["entity"]].append(v)
        self.sections: dict[str, list[dict]] = defaultdict(list)
        self.chunk: dict[str, dict] = {}
        self.vu_llm: dict[str, str] = {}
        for line in open(PROCESSED / "chunks.jsonl", encoding="utf-8"):
            c = json.loads(line)
            if c["type"] == "section":
                self.sections[c["section_id"]].append(c)
                self.chunk[c["chunk_id"]] = c
            else:
                self.vu_llm[c["vuid"]] = c["llm_text"]
        for parts in self.sections.values():
            parts.sort(key=lambda c: c["part_idx"])
        self.anchor = json.load(open(PROCESSED / "anchor_map.json", encoding="utf-8"))
        self.uses, self.extenders = vkxml_relations(RAW / "Vulkan-Docs" / "xml" / "vk.xml")

    def related(self, entity: str) -> list[str]:
        """Structures referenced by the entity (member/param types) and structures extending it via pNext,
        one level, only those that have VUs."""
        rel = (self.uses.get(entity, set()) | self.extenders.get(entity, set())) - {entity}
        return sorted(r for r in rel if r in self.by_entity)

    def entity_block(self, entity: str, with_section: str) -> dict:
        vus = sorted(self.by_entity[entity], key=lambda v: (not v["explicit"], v["vuid"]))
        parts = self.sections.get(with_section, [])
        return {
            "section_id": with_section if parts else None,
            "section_parts": [c["llm_text"] for c in parts],
            "vus": [{"vuid": v["vuid"], "explicit": v["explicit"], "text": v["text"]} for v in vus],
        }

    def ref_chunks(self, vu: dict, exclude_sections: set[str]) -> list[str]:
        out: list[str] = []
        for r in vu.get("refs", []):
            cid = self.anchor.get(r)
            c = self.chunk.get(cid) if cid else None
            if not c or c["section_id"] in exclude_sections or cid in out:
                continue
            out.append(cid)
            if len(out) >= MAX_REFS_PER_ITEM:
                break
        return out


VUID_OVERHEAD = 60  # chars per VU entry besides its text (vuid, keys, a same_text_as reference)


def content_units(corpus: Corpus, entity: str, section_id: str) -> dict[tuple, int]:
    """Distinct pieces of context an entity contributes, with their size: section parts and VU texts.
    Identical VU texts of different entities (e.g. the shared drawing-command VUs) are shown once
    per batch, so they share one key."""
    units: dict[tuple, int] = {}
    for c in corpus.sections.get(section_id, []):
        units[("sec", c["chunk_id"])] = len(c["llm_text"])
    for v in corpus.by_entity[entity]:
        units[("text", v["text"])] = len(v["text"])
        units[("vuid", v["vuid"])] = VUID_OVERHEAD
    return units


def build_batches(vuids: list[str], corpus: Corpus) -> list[list[str]]:
    """Group the sample by entity and pack entity groups into batches: first-fit decreasing on the
    size of the shared context, counting every distinct section part and VU text once per batch."""
    groups: dict[str, list[str]] = defaultdict(list)
    for v in sorted(vuids):
        groups[corpus.vu[v]["entity"]].append(v)
    need: dict[str, dict[tuple, int]] = {}
    for e, vs in groups.items():
        u = content_units(corpus, e, corpus.vu[vs[0]]["section_id"])
        for r in corpus.related(e):
            u.update(content_units(corpus, r, r))
        need[e] = u
    order = sorted(groups, key=lambda e: (-sum(need[e].values()), e))
    batches: list[dict] = []
    for e in order:
        for b in batches:
            add = sum(s for k, s in need[e].items() if k not in b["units"])
            if len(b["vuids"]) + len(groups[e]) <= MAX_ITEMS_PER_BATCH and b["chars"] + add <= MAX_CONTEXT_CHARS:
                b["vuids"] += groups[e]
                b["units"].update(need[e])
                b["chars"] += add
                break
        else:
            batches.append({"vuids": list(groups[e]), "units": dict(need[e]), "chars": sum(need[e].values())})
    return [sorted(b["vuids"]) for b in batches]


def dedupe_texts(entities: dict[str, dict]) -> int:
    """Replace repeated VU texts inside one batch with {"same_text_as": first vuid}. Returns the count."""
    first: dict[str, str] = {}
    n = 0
    for e in entities.values():
        for v in e["vus"]:
            t = v["text"]
            if t in first:
                del v["text"]
                v["same_text_as"] = first[t]
                n += 1
            else:
                first[t] = v["vuid"]
    return n


def batch_input(sample: str, n: int, vuids: list[str], asg: dict[str, dict], corpus: Corpus) -> dict:
    entities: dict[str, dict] = {}
    refs: dict[str, str] = {}
    items = []
    for v in vuids:
        vu = corpus.vu[v]
        e = vu["entity"]
        if e not in entities:
            entities[e] = corpus.entity_block(e, vu["section_id"])
        rel = corpus.related(e)
        for r in rel:
            if r not in entities:
                entities[r] = corpus.entity_block(r, r)
        ctx_sections = {b["section_id"] for b in entities.values() if b["section_id"]}
        ref_ids = corpus.ref_chunks(vu, ctx_sections)
        for cid in ref_ids:
            refs[cid] = corpus.chunk[cid]["llm_text"]
        a = asg[v]
        item = {
            "vuid": v,
            "entity": e,
            "entity_kind": vu["entity_kind"],
            "stratum": a["stratum"],
            "vu_text": vu["text"],
            "vu_chunk": corpus.vu_llm.get(v),
            "answer_type": a["answer_type"],
            "qids": a["qids"],
            "related_entities": rel,
            "ref_chunks": ref_ids,
        }
        if "expected_verdict" in a:
            item["expected_verdict"] = a["expected_verdict"]
        items.append(item)
    # the target entities first, so that the first occurrence of a shared text is under them
    targets = list(dict.fromkeys(i["entity"] for i in items))
    entities = {e: entities[e] for e in targets + sorted(set(entities) - set(targets))}
    dedupe_texts(entities)
    return {
        "sample": sample,
        "batch": n,
        "prompt_version": PROMPT_VERSION,
        "n_items": len(items),
        "items": items,
        "context": {"entities": entities, "ref_chunks": refs},
    }


def unanswerable_input(sample: str, cfg: dict, corpus: Corpus, exclude_entities: set[str]) -> dict:
    """Quotas of the three subtypes and candidate entities for the false-premise questions."""
    full = cfg["questions"]["unanswerable"]
    if sample == "pilot":
        n = cfg["questions"]["pilot"]["unanswerable"]
        rng = random.Random(stable_seed(cfg["seed"], sample, "unans_quota"))
        q = quotas(n, {k: v / sum(full.values()) for k, v in full.items()}, rng)
    else:
        q = dict(full)
    strata = {json.loads(l)["vuid"]: json.loads(l) for l in open(PROCESSED / "strata.jsonl", encoding="utf-8")}
    eligible = sorted({s["entity"] for s in strata.values()
                       if s["stratum"] and not s["excluded"] and s["entity_kind"] == "api" and s["entity"] not in exclude_entities})
    rng = random.Random(stable_seed(cfg["seed"], sample, "unans_entities"))
    k = 3 * (q["false_rule"] + q["false_behavior"])
    cands = rng.sample(eligible, min(k, len(eligible)))
    return {
        "sample": sample,
        "prompt_version": PROMPT_VERSION,
        "quotas": q,
        "qid_prefix": f"q{sample[0]}-u",
        "identifier_sources": [
            "data/processed/identifiers.json (by_kind, union over all vk.xml tags + main)",
            "data/processed/aliases.json",
            "data/external/spirv_identifiers.txt",
        ],
        "candidate_entities": {e: corpus.entity_block(e, e) for e in sorted(cands)},
    }


def prepare(sample: str) -> dict:
    cfg = load_config()
    samples = json.load(open(PROCESSED / "samples.json", encoding="utf-8"))
    if not samples.get("frozen"):
        raise RuntimeError("samples.json is not frozen")
    vuids = samples[sample]
    strata = {}
    for line in open(PROCESSED / "strata.jsonl", encoding="utf-8"):
        r = json.loads(line)
        strata[r["vuid"]] = r
    asg = assign(vuids, strata, cfg, sample)
    corpus = Corpus()
    batches = build_batches(vuids, corpus)
    bdir = GLOG / "batches" / sample
    bdir.mkdir(parents=True, exist_ok=True)
    sizes = []
    for n, bv in enumerate(batches, 1):
        inp = batch_input(sample, n, bv, asg, corpus)
        text = json.dumps(inp, ensure_ascii=False, indent=1)
        (bdir / f"batch_{n:03d}.input.json").write_text(text, encoding="utf-8")
        sizes.append({"batch": n, "items": len(bv), "entities": len(inp["context"]["entities"]), "chars": len(text)})
        for v in bv:
            asg[v]["batch"] = n
    other = "main" if sample == "pilot" else "pilot"
    excl = {corpus.vu[v]["entity"] for v in samples["main"] + samples["pilot"]}
    un = unanswerable_input(sample, cfg, corpus, excl)
    (bdir / "batch_unans.input.json").write_text(json.dumps(un, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {
        "sample": sample,
        "seed": cfg["seed"],
        "samples_sha256": samples["sha256"],
        "prompt_version": PROMPT_VERSION,
        "n_vus": len(vuids),
        "answer_type_by_stratum": {st: dict(Counter(a["answer_type"] for a in asg.values() if a["stratum"] == st)) for st in sorted({a["stratum"] for a in asg.values()})},
        "verdicts": dict(Counter(a.get("expected_verdict") for a in asg.values() if a["answer_type"] == "yes_no")),
        "gen_style": dict(Counter(a["gen_style"] for a in asg.values())),
        "batches": sizes,
        "unanswerable_quotas": un["quotas"],
        "not_in": other,
    }
    out = {"summary": summary, "assignments": {v: asg[v] for v in sorted(asg)}}
    (GLOG / f"{sample}_assignments.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def prepare_regen(sample: str) -> dict:
    """New batch(es) for the VUs listed in <sample>_validation.json `regenerate_vuids`, with the same
    assignments and qids. `validate` keeps, for every VU, the lines of the latest batch containing it."""
    report = json.load(open(GLOG / f"{sample}_validation.json", encoding="utf-8"))
    vuids = report["regenerate_vuids"]
    if not vuids:
        return {"sample": sample, "regenerate": 0}
    asg_file = GLOG / f"{sample}_assignments.json"
    data = json.load(open(asg_file, encoding="utf-8"))
    asg = data["assignments"]
    bdir = GLOG / "batches" / sample
    last = max(int(p.name[6:9]) for p in bdir.glob("batch_[0-9][0-9][0-9].input.json"))
    corpus = Corpus()
    made = []
    for n, bv in enumerate(build_batches(vuids, corpus), last + 1):
        inp = batch_input(sample, n, bv, asg, corpus)
        inp["regenerates"] = {v: asg[v]["batch"] for v in bv}
        (bdir / f"batch_{n:03d}.input.json").write_text(json.dumps(inp, ensure_ascii=False, indent=1), encoding="utf-8")
        for v in bv:
            asg[v].setdefault("previous_batches", []).append(asg[v]["batch"])
            asg[v]["batch"] = n
        made.append({"batch": n, "items": len(bv)})
    asg_file.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"sample": sample, "regenerate": len(vuids), "batches": made}
