"""Stage 2: stratum assignment, exclusions and sampling of VUs (PLAN §4 Stage 2, §9.3).

Inputs:  data/processed/vuids.jsonl (condition DNF from adoc), registry.json, aliases.json,
         vuid_history.json, data/external/gpuinfo_snapshot.json, config `strata`.
Outputs: data/processed/strata.jsonl  one record per explicit VU: stratum, base stratum, flags, exclusion
         data/processed/samples.json  main / pilot VUID lists with the sampling parameters
         reports/strata_table.md      "stratum x available x selected" and breakdowns

Access path of a VU = condition DNF AND entity-origin DNF (origin = core version of the entity OR
any extension that defines it). For every clause:
  only versions                       -> core, version = max(versions)
  all extensions promoted to core     -> core, version = max(versions, promotion versions), cond_ext_only_promoted
  otherwise                           -> extension path over the non-promoted extensions
Any core clause -> core path with the minimum version: 1.0 -> core_1_0, 1.1+ -> core_promoted.
Otherwise the clause with the highest popularity (min coverage of its non-promoted extensions,
vendor extension = 0) decides: >= threshold and only KHR/EXT -> ext_popular, else ext_niche.
`recent` overrides everything when the VU first appeared after the recent cutoff.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import date

from vkrag.conditions import CORE, DNF, conj, from_str, simplify_versions, version_of
from vkrag.config import EXTERNAL, PROCESSED, ROOT, load_config

STRATA = ("recent", "ext_niche", "ext_popular", "core_promoted", "core_1_0")
BASE_STRATA = STRATA[1:]
NON_VENDOR = ("KHR", "EXT")


class Registry:
    def __init__(self, registry: dict, aliases: dict[str, str], coverage: dict[str, float]):
        self.entities = registry["entities"]
        self.ext = registry["extensions"]
        self.aliases = aliases
        self.coverage = coverage

    def entity(self, name: str) -> dict | None:
        return self.entities.get(name) or self.entities.get(self.aliases.get(name, ""))

    def promoted_core(self, ext: str, seen: frozenset = frozenset()) -> tuple[int, int] | None:
        """Core version an extension is (transitively) promoted to, else None."""
        info = self.ext.get(ext)
        if not info or not info.get("promotedto") or ext in seen:
            return None
        target = info["promotedto"]
        v = version_of(target)
        return v if v else self.promoted_core(target, seen | {ext})

    def is_vendor(self, ext: str) -> bool:
        return ext.split("_")[1] not in NON_VENDOR

    def popularity(self, ext: str) -> float:
        return 0.0 if self.is_vendor(ext) else self.coverage.get(ext, 0.0)


def origin_dnf(reg: Registry, entity: str) -> tuple[DNF, bool]:
    """Entity origin as DNF: {VK_VERSION_x_y} OR {ext} for every defining extension.
    Entities outside vk.xml (SPIR-V, built-ins) or without origin -> core 1.0, flagged."""
    e = reg.entity(entity)
    clauses = []
    if e:
        if e.get("core_version"):
            clauses.append(frozenset({"VK_VERSION_" + e["core_version"].replace(".", "_")}))
        clauses += [frozenset({x}) for x in e.get("extensions", [])]
    if not clauses:
        return frozenset({frozenset({"VK_VERSION_1_0"})}), True
    return frozenset(clauses), False


def classify_clause(reg: Registry, clause: frozenset[str]) -> dict:
    vers = [v for v in (version_of(a) for a in clause) if v]
    exts = sorted(a for a in clause if not version_of(a))
    unknown = [x for x in exts if x not in reg.ext]
    if unknown:
        return {"path": "unknown", "unknown": unknown}
    promoted = {x: reg.promoted_core(x) for x in exts}
    rest = [x for x in exts if promoted[x] is None]
    if not rest:
        v = max(vers + [p for p in promoted.values() if p] or [(1, 0)])
        return {"path": "core", "version": v, "ext_only_promoted": bool(exts)}
    pop = min(reg.popularity(x) for x in rest)
    return {"path": "ext", "extensions": rest, "popularity": pop,
            "non_vendor": all(not reg.is_vendor(x) for x in rest)}


def base_stratum(reg: Registry, cond: DNF, entity: str, threshold: float) -> dict:
    origin, origin_unknown = origin_dnf(reg, entity)
    dnf = simplify_versions(conj(cond, origin))
    paths = [classify_clause(reg, c) for c in sorted(dnf, key=lambda c: sorted(c))]
    out: dict = {"origin_unknown": origin_unknown, "access_dnf": sorted("+".join(sorted(c)) for c in dnf)}
    unknown = sorted({u for p in paths if p["path"] == "unknown" for u in p["unknown"]})
    if unknown:
        out.update(base=None, unknown_names=unknown)
        return out
    core = [p for p in paths if p["path"] == "core"]
    if core:
        best = min(core, key=lambda p: p["version"])
        out.update(base="core_1_0" if best["version"] == (1, 0) else "core_promoted",
                   core_version="%d.%d" % best["version"], cond_ext_only_promoted=best["ext_only_promoted"])
        return out
    best = max((p for p in paths if p["path"] == "ext"), key=lambda p: (p["popularity"], p["non_vendor"], p["extensions"]))
    popular = best["popularity"] >= threshold and best["non_vendor"]
    out.update(base="ext_popular" if popular else "ext_niche", path_extensions=best["extensions"],
               popularity=round(best["popularity"], 4))
    return out


def exclusion(reg: Registry, cond: DNF, entity: str) -> tuple[str | None, dict]:
    """Reason to exclude a VU from questions (it stays in the corpus) and informational flags."""
    names = {a for c in cond for a in c if not version_of(a)}
    flags = {}
    e = reg.entity(entity)
    ent_exts = (e or {}).get("extensions", []) if not (e or {}).get("core_version") else []
    if any(reg.ext.get(x, {}).get("provisional") for x in names):
        return "provisional_condition", flags
    if ent_exts and all(reg.ext.get(x, {}).get("provisional") for x in ent_exts):
        return "provisional_entity", flags
    if any(reg.ext.get(x, {}).get("obsoletedby") for x in ent_exts):
        return "obsoleted_entity", flags
    if any(reg.ext.get(x, {}).get("specialuse") for x in ent_exts):
        return "specialuse_entity", flags
    if any(reg.ext.get(x, {}).get("specialuse") for x in names):
        flags["cond_specialuse"] = True
    if any(reg.ext.get(x, {}).get("deprecatedby") is not None for x in names | set(ent_exts)):
        flags["deprecated"] = True
    return None, flags


def recent_cutoff(cfg: dict) -> tuple[str | None, dict]:
    """Earlier of the answerer cutoffs (PLAN §4 Stage 2); None while any of them is unknown."""
    cut = cfg["strata"]["recent_cutoff"]
    dates = {k: v.get("date") for k, v in cut.items()}
    if any(d is None for d in dates.values()):
        return None, dates
    return min(str(d) for d in dates.values()), dates


def stable_seed(seed: int, stratum: str) -> int:
    return seed + int(hashlib.sha256(stratum.encode()).hexdigest()[:8], 16)


def sample(cands: list[dict], per_stratum: dict[str, int], max_per_entity: int, seed: int,
           used_vuids: set[str] = frozenset(), used_classes: set[str] = frozenset()) -> list[dict]:
    """PLAN §9.3 sampling: strata in ascending candidate count, shuffled with a stable per-stratum
    seed, greedy: <= max_per_entity VUs per entity (across strata), one VU per equivalence class."""
    by = defaultdict(list)
    for r in sorted(cands, key=lambda r: (r["stratum"], r["entity"], r["vuid"])):
        if r["vuid"] not in used_vuids and r["equiv_class_id"] not in used_classes:
            by[r["stratum"]].append(r)
    ent_count: Counter = Counter()
    classes: set[str] = set()
    picked = []
    for st in sorted(by, key=lambda s: (len(by[s]), s)):
        pool = list(by[st])
        random.Random(stable_seed(seed, st)).shuffle(pool)
        n = 0
        for r in pool:
            if n >= per_stratum.get(st, 0):
                break
            if ent_count[r["entity"]] >= max_per_entity or r["equiv_class_id"] in classes:
                continue
            ent_count[r["entity"]] += 1
            classes.add(r["equiv_class_id"])
            picked.append(r)
            n += 1
    return sorted(picked, key=lambda r: (r["stratum"], r["entity"], r["vuid"]))


def load_inputs():
    cfg = load_config()
    reg = json.loads((PROCESSED / "registry.json").read_text(encoding="utf-8"))
    aliases = json.loads((PROCESSED / "aliases.json").read_text(encoding="utf-8"))["alias_to_target"]
    snap = json.loads((ROOT / cfg["strata"]["gpuinfo_snapshot"]).read_text(encoding="utf-8"))
    hist = json.loads((PROCESSED / "vuid_history.json").read_text(encoding="utf-8"))
    vus = [json.loads(line) for line in open(PROCESSED / "vuids.jsonl", encoding="utf-8")]
    return cfg, Registry(reg, aliases, snap["extensions"]), snap, hist, vus


def assign(cfg: dict, reg: Registry, hist: dict, vus: list[dict]) -> tuple[list[dict], dict]:
    thr = cfg["strata"]["popularity_threshold"]
    cutoff, _ = recent_cutoff(cfg)
    if cutoff and cutoff < hist["window_start"]:
        raise ValueError(f"recent cutoff {cutoff} is before the history window {hist['window_start']}")
    out, log = [], Counter()
    for v in vus:
        if not v["explicit"]:
            continue
        cond = from_str(v["condition"]) if v.get("condition") is not None else None
        rec = {k: v[k] for k in ("vuid", "entity", "entity_kind", "equiv_class_id", "equiv_class_size", "condition")}
        h = hist["vuids"].get(v["vuid"])
        rec.update(first_tag=h and h["first_tag"], first_date=h and h["first_date"],
                   before_window=bool(h and h["before_window"]),
                   text_changed_recently=bool(h and h.get("text_changed_recently")),
                   new_in_last_n=bool(h and h.get("new_in_last_n")))
        if cond is None:
            rec.update(stratum=None, base_stratum=None, excluded="condition_missing")
            log["condition_missing"] += 1
            out.append(rec)
            continue
        b = base_stratum(reg, cond, v["entity"], thr)
        rec["base_stratum"] = b.pop("base")
        rec.update(b)
        reason, flags = exclusion(reg, cond, v["entity"])
        rec.update(flags)
        if h is None:
            reason = reason or "undated"
        if rec["base_stratum"] is None:
            reason = reason or "unknown_condition_name"
        is_recent = bool(cutoff and rec["first_date"] and not rec["before_window"] and rec["first_date"] > cutoff)
        rec["stratum"] = "recent" if is_recent else rec["base_stratum"]
        rec["excluded"] = reason
        log[reason or "eligible"] += 1
        out.append(rec)
    return out, dict(log)


def table(recs: list[dict], main: list[dict], pilot: list[dict]) -> str:
    elig = [r for r in recs if not r["excluded"]]
    avail = Counter(r["stratum"] for r in elig)
    sel_m = Counter(r["stratum"] for r in main)
    sel_p = Counter(r["stratum"] for r in pilot)
    ents = defaultdict(set)
    for r in elig:
        ents[r["stratum"]].add(r["entity"])
    total = sum(avail.values())
    lines = ["| stratum | available VUs | entities | weight | main | pilot |", "|---|---|---|---|---|---|"]
    for s in STRATA:
        lines.append(f"| {s} | {avail.get(s, 0)} | {len(ents.get(s, ()))} | {avail.get(s, 0) / total:.3f} | {sel_m.get(s, 0)} | {sel_p.get(s, 0)} |")
    lines.append(f"| **total** | {total} | {len(set().union(*ents.values()))} | 1.000 | {len(main)} | {len(pilot)} |")
    return "\n".join(lines)


def crosstab(rows: list[dict], a: str, b: str, a_vals=None) -> str:
    c = Counter((r.get(a), r.get(b)) for r in rows)
    av = a_vals or sorted({k[0] for k in c}, key=str)
    bv = sorted({k[1] for k in c}, key=str)
    lines = [f"| {a} \\ {b} | " + " | ".join(map(str, bv)) + " |", "|---" * (len(bv) + 1) + "|"]
    for x in av:
        lines.append(f"| {x} | " + " | ".join(str(c.get((x, y), 0)) for y in bv) + " |")
    return "\n".join(lines)


def samples_hash(main: list[str], pilot: list[str]) -> str:
    return hashlib.sha256(json.dumps({"main": main, "pilot": pilot}, sort_keys=True).encode()).hexdigest()


def freeze() -> dict:
    """Mark samples.json as frozen (PLAN Stage 2): later `vkrag strata` runs must reproduce it exactly."""
    path = PROCESSED / "samples.json"
    s = json.loads(path.read_text(encoding="utf-8"))
    if s.get("provisional"):
        raise ValueError("cannot freeze a provisional sample (recent cutoff not set)")
    s.update(frozen=True, frozen_at=date.today().isoformat(), sha256=samples_hash(s["main"], s["pilot"]))
    path.write_text(json.dumps(s, indent=1), encoding="utf-8")
    return s


def run(allow_no_recent: bool = False) -> dict:
    cfg, reg, snap, hist, vus = load_inputs()
    st = cfg["strata"]
    cutoff, cut_dates = recent_cutoff(cfg)
    recs, log = assign(cfg, reg, hist, vus)
    with open(PROCESSED / "strata.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in recs:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    elig = [r for r in recs if not r["excluded"]]
    main: list[dict] = []
    pilot: list[dict] = []
    sampled = cutoff is not None or allow_no_recent
    if sampled:
        strata_used = [s for s in STRATA if cutoff or s != "recent"]
        main = sample(elig, {s: st["per_stratum"] for s in strata_used}, st["max_per_entity"], cfg["seed"])
        n_pilot = cfg["questions"]["pilot"]["answerable"]
        per = {s: n_pilot // len(strata_used) + (1 if i < n_pilot % len(strata_used) else 0) for i, s in enumerate(strata_used)}
        pilot = sample(elig, per, st["max_per_entity"], cfg["seed"] + 1,
                       used_vuids={r["vuid"] for r in main}, used_classes={r["equiv_class_id"] for r in main})
        path = PROCESSED / "samples.json"
        prev = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        new_hash = samples_hash([r["vuid"] for r in main], [r["vuid"] for r in pilot])
        if prev.get("frozen"):
            if prev["sha256"] != new_hash:
                raise RuntimeError("samples.json is frozen and the recomputed sample differs; inputs changed. "
                                   "Unfreeze explicitly (PLAN §10 entry) before resampling.")
            sampled_frozen = prev
        else:
            sampled_frozen = None
        if sampled_frozen is None:
            path.write_text(json.dumps({
                "provisional": cutoff is None,
                "recent_cutoff": cutoff, "recent_cutoff_by_model": cut_dates, "seed": cfg["seed"],
                "per_stratum": st["per_stratum"], "max_per_entity": st["max_per_entity"],
                "popularity_threshold": st["popularity_threshold"], "gpuinfo_date": snap["date"],
                "main": [r["vuid"] for r in main], "pilot": [r["vuid"] for r in pilot],
            }, indent=1), encoding="utf-8")
    report = [
        "# Stage 2: strata",
        "",
        f"Generated by `vkrag strata` on {date.today().isoformat()}. Spec tag `{cfg['spec']['tag']}`, "
        f"gpuinfo snapshot {snap['date']} ({', '.join(snap['platforms'])}, {snap['window']}, combine `{snap['combine']}`), "
        f"popularity threshold {st['popularity_threshold']}, seed {cfg['seed']}.",
        "",
        f"Recent cutoff: **{cutoff or 'not set'}** (per model: {cut_dates}). "
        + ("" if cutoff else "Without a cutoff there is no `recent` stratum; the sample below is a provisional preview and is not frozen."),
        "",
        "## Eligibility",
        "",
        "| status | explicit VUs |", "|---|---|",
        *[f"| {k} | {v} |" for k, v in sorted(log.items(), key=lambda kv: -kv[1])],
        "",
        "## Stratum x available x selected",
        "",
        "Weight = share of the stratum among eligible explicit VUs (used only for the weighted sensitivity aggregate).",
        "",
        table(recs, main, pilot) if sampled else table(recs, [], []),
        "",
        "## Base stratum x entity kind (eligible)",
        "",
        crosstab(elig, "base_stratum", "entity_kind", list(BASE_STRATA)),
        "",
        "## First tag date (eligible, inside the history window) x base stratum",
        "",
        crosstab([dict(r, year=(r["first_date"] or "")[:7] if not r["before_window"] else "before window") for r in elig],
                 "year", "base_stratum"),
        "",
        "## Flags (eligible)",
        "",
        f"- `text_changed_recently`: {sum(r['text_changed_recently'] for r in elig)}",
        f"- `new_in_last_n` (absent {cfg['strata']['text_change']['last_n_tags']} tags ago): {sum(r['new_in_last_n'] for r in elig)}",
        f"- `cond_ext_only_promoted`: {sum(bool(r.get('cond_ext_only_promoted')) for r in elig)}",
        f"- `deprecated`: {sum(bool(r.get('deprecated')) for r in elig)}",
        f"- `cond_specialuse`: {sum(bool(r.get('cond_specialuse')) for r in elig)}",
        f"- `origin_unknown` (entity outside vk.xml, treated as core 1.0): {sum(r['origin_unknown'] for r in elig)}",
    ]
    if sampled:
        report += ["", "## Main sample: stratum x entity kind", "", crosstab(main, "stratum", "entity_kind", [s for s in STRATA]),
                   "", f"Distinct entities in main: {len({r['entity'] for r in main})}; "
                   f"with text_changed_recently: {sum(r['text_changed_recently'] for r in main)}",
                   "", "## Main sample: stratum x base stratum", "", crosstab(main, "stratum", "base_stratum", list(STRATA)),
                   "", "## Cutoff sensitivity (main sample)", "",
                   "| cutoff | recent VUs available | main: recent -> not recent | main: not recent -> recent |", "|---|---|---|---|"]
        for c in st.get("recent_cutoff_sensitivity", []):
            isr = lambda r, c=c: bool(r["first_date"] and not r["before_window"] and r["first_date"] > c)  # noqa: E731
            report.append(f"| {c} | {sum(isr(r) for r in elig)} | {sum(1 for r in main if r['stratum'] == 'recent' and not isr(r))} | "
                          f"{sum(1 for r in main if r['stratum'] != 'recent' and isr(r))} |")
    (ROOT / "reports" / "strata_table.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return {"log": log, "cutoff": cutoff, "main": len(main), "pilot": len(pilot),
            "available": dict(Counter(r["stratum"] for r in elig))}
