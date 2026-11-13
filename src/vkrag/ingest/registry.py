"""Stage 1, items 7-8: vk.xml -> aliases, entity origin, identifiers.

Outputs:
  data/processed/aliases.json      {name: canonical} and the reverse map
  data/processed/registry.json     entities: core_version | extensions, extension flags
  data/processed/identifiers.json  union of vk.xml identifiers over all tags + main
"""

from __future__ import annotations

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict

from vkrag.conditions import version_of
from vkrag.config import PROCESSED, RAW, load_config

DOCS = RAW / "Vulkan-Docs"


def _vulkan_api(attr: str | None) -> bool:
    """The api/supported attribute allows regular Vulkan (not only vulkansc)."""
    return attr is None or "vulkan" in attr.split(",")


def _xml_at(tag: str | None) -> ET.Element:
    if tag is None:
        return ET.parse(DOCS / "xml" / "vk.xml").getroot()
    for path in ("xml/vk.xml", "src/spec/vk.xml"):  # old tags kept the registry under src/spec
        r = subprocess.run(["git", "-C", str(DOCS), "show", f"{tag}:{path}"], capture_output=True)
        if r.returncode == 0:
            return ET.fromstring(r.stdout)
    raise subprocess.CalledProcessError(128, f"git show {tag}:vk.xml")


def collect_identifiers(root: ET.Element) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {k: set() for k in ("commands", "types", "enums", "members", "extensions", "features")}
    for t in root.iter("type"):
        name = t.get("name") or (t.findtext("name"))
        if name:
            out["types"].add(name)
        for m in t.findall("member"):
            mn = m.findtext("name")
            if mn:
                out["members"].add(mn)
    for c in root.iter("command"):
        name = c.get("name") or c.findtext("proto/name")
        if name:
            out["commands"].add(name)
        for p in c.findall("param"):
            pn = p.findtext("name")
            if pn:
                out["members"].add(pn)
    for e in root.iter("enum"):
        if e.get("name"):
            out["enums"].add(e.get("name"))
    for x in root.iter("extension"):
        out["extensions"].add(x.get("name"))
    for f in root.iter("feature"):
        if f.get("name", "").startswith("VK_") and f.get("number"):
            out["features"].add(f.get("name"))
    return out


def parse_registry(root: ET.Element) -> dict:
    aliases: dict[str, str] = {}
    for el in list(root.iter("command")) + list(root.iter("type")) + list(root.iter("enum")):
        name, alias = el.get("name"), el.get("alias")
        if name and alias:
            aliases[name] = alias

    def canonical(n: str) -> str:
        seen = set()
        while n in aliases and n not in seen:
            seen.add(n)
            n = aliases[n]
        return n

    core: dict[str, tuple[int, int]] = {}
    for f in root.findall("feature"):
        if not _vulkan_api(f.get("api")):
            continue
        ver = version_of(f.get("name", ""))
        if not ver:
            continue
        for req in f.findall("require"):
            if not _vulkan_api(req.get("api")):
                continue
            for el in req:
                n = el.get("name")
                if n and el.tag in ("command", "type", "enum"):
                    if n not in core or ver < core[n]:
                        core[n] = ver

    ext_info: dict[str, dict] = {}
    ent_exts: dict[str, set[str]] = defaultdict(set)
    for x in root.find("extensions"):
        if not _vulkan_api(x.get("supported")) or x.get("supported") == "disabled":
            continue
        name = x.get("name")
        ext_info[name] = {
            "author": x.get("author"),
            "type": x.get("type"),
            "vendor_prefix": name.split("_")[1],
            "provisional": x.get("provisional") == "true",
            "promotedto": x.get("promotedto") or None,
            "deprecatedby": x.get("deprecatedby"),  # "" = deprecated without replacement, None = not deprecated
            "obsoletedby": x.get("obsoletedby"),
            "specialuse": x.get("specialuse") or None,
            "ratified": "vulkan" in (x.get("ratified") or "").split(","),
            "platform": x.get("platform"),
        }
        for req in x.findall("require"):
            if not _vulkan_api(req.get("api")):
                continue
            for el in req:
                n = el.get("name")
                if n and el.tag in ("command", "type"):
                    ent_exts[n].add(name)

    entities = {}
    for n in set(core) | set(ent_exts):
        cv = core.get(n) or core.get(canonical(n))
        entities[n] = {
            "core_version": f"{cv[0]}.{cv[1]}" if cv else None,
            "extensions": sorted(ent_exts.get(n, ())),
            "canonical": canonical(n),
        }
    return {"aliases": aliases, "extensions": ext_info, "entities": entities}


def _all_tags() -> list[str]:
    out = subprocess.run(["git", "-C", str(DOCS), "tag"], check=True, capture_output=True, text=True).stdout.split()
    return sorted(t for t in out if re.match(r"^v1\.\d+\.\d+(-core)?$", t))


def _tag_key(t: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", t))


def build_identifiers(tags: list[str]) -> dict:
    """Union over all tags and origin/main.

    outdated: present in tags not newer than the current one but absent from it (old names);
    newer:    present only in tags newer than the current one / main.
    """
    current = load_config()["spec"]["tag"]
    union: dict[str, set[str]] = defaultdict(set)
    older: set[str] = set()
    newer: set[str] = set()
    current_ids: set[str] = set()
    skipped = []
    for tag in tags + ["origin/main"]:
        try:
            root = _xml_at(tag)
        except subprocess.CalledProcessError:
            skipped.append(tag)
            continue
        ids = collect_identifiers(root)
        flat = set().union(*ids.values())
        for k, v in ids.items():
            union[k] |= v
        if tag == current:
            current_ids = flat
        elif tag == "origin/main" or _tag_key(tag) > _tag_key(current):
            newer |= flat
        else:
            older |= flat
    all_ids = set().union(*union.values())
    return {
        "tags_scanned": len(tags) + 1 - len(skipped),
        "tags_skipped": skipped,
        "by_kind": {k: sorted(v) for k, v in union.items()},
        "outdated": sorted(older - current_ids),
        "newer": sorted(newer - current_ids - older),
        "count": len(all_ids),
    }


def run(history: bool = True) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    tag = load_config()["spec"]["tag"]
    reg = parse_registry(_xml_at(tag))
    aliases = reg.pop("aliases")
    rev: dict[str, list[str]] = defaultdict(list)
    for a, c in aliases.items():
        rev[c].append(a)
    (PROCESSED / "aliases.json").write_text(
        json.dumps({"alias_to_target": aliases, "target_to_aliases": {k: sorted(v) for k, v in rev.items()}}, indent=1, sort_keys=True),
        encoding="utf-8",
    )
    (PROCESSED / "registry.json").write_text(json.dumps(reg, indent=1, sort_keys=True), encoding="utf-8")
    print(f"aliases={len(aliases)} entities={len(reg['entities'])} extensions={len(reg['extensions'])}")
    if history:
        ids = build_identifiers(_all_tags())
        (PROCESSED / "identifiers.json").write_text(json.dumps(ids, indent=0), encoding="utf-8")
        print(f"identifiers: {ids['count']} over {ids['tags_scanned']} tags; outdated={len(ids['outdated'])} newer={len(ids['newer'])}")
