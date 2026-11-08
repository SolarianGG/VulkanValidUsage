"""Stage 1, items 4-5: validusage.json -> normalized VU records (no strata or classes yet).

validusage.json is the only source of VU text. Explicit/implicit is decided by the VUID suffix.
"""
from __future__ import annotations

import json
from collections import Counter

from vkrag.config import BUILD, PROCESSED
from vkrag.normalize import html_to_text

IMPLICIT_SUFFIXES = {
    "parameter", "sType", "pNext", "recording", "cmdpool", "videocoding", "arraylength", "parent",
    "suspended", "commonparent", "unique", "renderpass", "zerobitmask", "queuecount", "bufferlevel", "queuetype",
}
SPIRV_ENTITIES = {"RuntimeSpirv", "StandaloneSpirv"}


def split_vuid(vuid: str) -> tuple[str, str, str]:
    """VUID-<entity>-<param>-<suffix>. The entity name inside a VUID may be an old one (pre-promotion alias)."""
    parts = vuid.split("-")
    if parts[0] != "VUID" or len(parts) < 3:
        raise ValueError(vuid)
    entity = parts[1]
    if len(parts) == 3:
        return entity, "", parts[2]  # VUID-X-commonparent: no parameter
    return entity, "-".join(parts[2:-1]), parts[-1]


def load_records() -> tuple[list[dict], dict]:
    vu = json.loads((BUILD / "validusage.json").read_text(encoding="utf-8"))
    registry = json.loads((PROCESSED / "registry.json").read_text(encoding="utf-8"))
    conds = json.loads((PROCESSED / "vu_conditions.json").read_text(encoding="utf-8"))
    ents = registry["entities"]
    recs, unknown_suffix, stats = [], Counter(), Counter()
    for entity in sorted(vu["validation"]):
        for cond_key, lst in sorted(vu["validation"][entity].items()):
            for e in lst:
                vuid = e["vuid"]
                vuid_entity, param, suffix = split_vuid(vuid)
                if vuid_entity != entity:
                    stats["vuid_entity_differs"] += 1
                explicit = suffix.isdigit()
                if not explicit and suffix not in IMPLICIT_SUFFIXES:
                    unknown_suffix[suffix] += 1
                text, refs = html_to_text(e["text"])
                kind = "spirv" if entity in SPIRV_ENTITIES else ("api" if entity in ents else "builtin")
                origin = ents.get(entity, {})
                c = conds.get(vuid)
                if explicit and c is None:
                    stats["explicit_without_adoc_condition"] += 1
                recs.append({
                    "vuid": vuid,
                    "entity": entity,
                    "vuid_entity": vuid_entity,
                    "entity_kind": kind,
                    "parameter": param,
                    "suffix": suffix,
                    "explicit": explicit,
                    "suffix_num": int(suffix) if explicit else None,
                    "json_condition": cond_key,
                    "condition": c["condition"] if c else None,
                    "condition_raw": c["condition_raw"] if c else None,
                    "adoc_source": c["sources"][0] if c else None,
                    "refpage": c["refpage"] if c else None,
                    "entity_core_version": origin.get("core_version"),
                    "entity_extensions": origin.get("extensions", []),
                    "page": e.get("page"),
                    "text": text,
                    "text_html": e["text"],
                    "refs": refs,
                })
                stats[f"{kind}_{'explicit' if explicit else 'implicit'}"] += 1
    stats["unknown_suffixes"] = dict(unknown_suffix)
    return recs, dict(stats)


def run() -> dict:
    recs, stats = load_records()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED / "vu_base.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats["total"] = len(recs)
    return stats
