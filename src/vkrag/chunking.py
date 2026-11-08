"""Stage 1, items 10-14: chunks, metadata, length limits, coverage.

Outputs (data/processed/):
  chunks.jsonl         section parts + one chunk per VU
  vuids.jsonl          VU records with equivalence classes and parent section
  coverage_report.json VUID -> chunk mapping, json vs Headers diff, length stats
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict

from vkrag import tokens
from vkrag.conditions import from_str, version_of
from vkrag.config import BUILD, PROCESSED, RAW, load_config
from vkrag.equivalence import assign_classes
from vkrag.ingest.sections import Unit, parse_sections


def _h(s: str, n: int = 12) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]


# ---------------------------------------------------------------- VU context header


def _atom_label(a: str) -> str:
    v = version_of(a)
    return f"Vulkan {v[0]}.{v[1]}" if v else a


LABEL_MAX_ATOMS = 3


def availability_label(rec: dict) -> str:
    """Compact availability tag for the VU header: distinct extensions/versions of the condition.

    The full DNF stays in metadata (`condition`); spelling out every clause bloats the header
    (some draw-indirect VUs have 5+ clauses of 5 atoms each)."""
    cond = rec.get("condition")
    if cond and cond != "core" and cond != "VK_VERSION_1_0":
        atoms = sorted({a for cl in from_str(cond) for a in cl}, key=lambda a: (version_of(a) is not None, a))
        labels = [_atom_label(a) for a in atoms]
        if len(labels) > LABEL_MAX_ATOMS:
            return ", ".join(labels[:LABEL_MAX_ATOMS]) + f" (+{len(labels) - LABEL_MAX_ATOMS} more)"
        return ", ".join(labels)
    if rec.get("entity_core_version"):
        return f"Vulkan {rec['entity_core_version']}"
    if rec.get("entity_extensions"):
        return " or ".join(rec["entity_extensions"])
    return "Vulkan 1.0" if rec["entity_kind"] == "api" else "SPIR-V"


def vu_texts(rec: dict) -> tuple[str, str]:
    head = [f"[{rec['entity']}]"]
    if rec["parameter"] and rec["parameter"] != "None":
        head.append(f"[{rec['parameter']}]")
    head.append(f"[{availability_label(rec)}]")
    index_text = " ".join(head) + "\n" + rec["text"]
    llm_text = f"{rec['vuid']}\n{index_text}"
    return index_text, llm_text


# ---------------------------------------------------------------- section splitting


def _split_long_block(block: str, budget: int) -> list[str]:
    """Split an atomic block (big table / list) by lines, then hard-split oversized lines by words."""
    out, cur = [], []
    for line in block.split("\n"):
        if tokens.count_max(line) > budget:
            words, piece = line.split(" "), []
            for w in words:
                if piece and tokens.count_max(" ".join(piece + [w])) > budget:
                    out.append(" ".join(piece))
                    piece = []
                piece.append(w)
            if piece:
                line = " ".join(piece)
            else:
                continue
        if cur and tokens.count_max("\n".join(cur + [line])) > budget:
            out.append("\n".join(cur))
            cur = []
        cur.append(line)
    if cur:
        out.append("\n".join(cur))
    return out


def split_unit(u: Unit, max_tokens: int) -> list[str]:
    # refpage: path = enclosing sections, title = entity; prose: path = parent sections, title = section
    header = "[" + " > ".join(u.path + [u.title]) + "]"
    budget = max_tokens - tokens.count_max(header + "\n") - 2
    paras = [p for p in re.split(r"\n{2,}", u.text) if p.strip()]
    blocks: list[str] = []
    for p in paras:
        blocks.extend(_split_long_block(p, budget) if tokens.count_max(p) > budget else [p])
    parts, cur, cur_tok = [], [], 0
    for b in blocks:
        bt = tokens.count_max(b)
        if cur and cur_tok + bt + 2 > budget:
            parts.append(cur)
            cur, cur_tok = [], 0
        cur.append(b)
        cur_tok += bt + 2
    if cur:
        parts.append(cur)
    return [header + "\n" + "\n\n".join(p) for p in parts]


# ---------------------------------------------------------------- main


def _load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _headers_diff(tag: str, built: set[str]) -> dict:
    import subprocess

    data = subprocess.run(["git", "-C", str(RAW / "Vulkan-Headers"), "show", f"{tag}:registry/validusage.json"],
                          check=True, capture_output=True).stdout
    hv = json.loads(data)["validation"]
    hset = {e["vuid"] for b in hv.values() for lst in b.values() for e in lst}
    return {"headers_total": len(hset), "only_in_build": sorted(built - hset), "only_in_headers": sorted(hset - built)}


def run() -> dict:
    cfg = load_config()
    max_tokens = cfg["corpus"]["max_chunk_tokens"]
    recs = _load_jsonl(PROCESSED / "vu_base.jsonl")
    aliases = json.loads((PROCESSED / "aliases.json").read_text(encoding="utf-8"))
    registry = json.loads((PROCESSED / "registry.json").read_text(encoding="utf-8"))

    eq_report = assign_classes(recs, aliases["target_to_aliases"], cfg["corpus"].get("equiv_text_placeholder", True))
    units, sec_stats, heading_fallback = parse_sections(set(registry["entities"]))

    chunks: list[dict] = []
    anchor_to_chunk: dict[str, str] = {}
    vuid_to_section: dict[str, str] = {}
    section_first_chunk: dict[str, str] = {}
    for u in units:
        parts = split_unit(u, max_tokens)
        for i, text in enumerate(parts):
            cid = f"sec-{_h(u.source_anchor + '|' + str(i) + '|' + _h(text, 16))}"
            chunks.append({
                "chunk_id": cid, "type": "section", "section_kind": u.kind, "entity": u.entity,
                "section_id": u.source_anchor, "part_idx": i, "n_parts": len(parts),
                "title": u.title, "path": u.path, "source_anchor": u.source_anchor,
                "refs": u.refs, "vuids_in_section": u.vuids_in_section if i == 0 else [],
                "index_text": text, "llm_text": text,
            })
            if i == 0:
                section_first_chunk[u.source_anchor] = cid
        # anchors -> first part (anchors inside later parts are rare; first part is the safe target)
        for a in u.anchors:
            anchor_to_chunk.setdefault(a, section_first_chunk[u.source_anchor])
        for v in u.vuids_in_section:
            vuid_to_section[v] = u.source_anchor
    for heading, target in heading_fallback.items():
        anchor_to_chunk.setdefault(heading, section_first_chunk[target])

    by_vuid = {r["vuid"]: r for r in recs}
    for r in recs:
        r["section_id"] = vuid_to_section.get(r["vuid"])
        index_text, llm_text = vu_texts(r)
        chunks.append({
            "chunk_id": r["vuid"], "type": "vu", "entity": r["entity"], "entity_kind": r["entity_kind"],
            "vuid": r["vuid"], "explicit": r["explicit"], "equiv_class_id": r["equiv_class_id"],
            "section_id": r["section_id"], "part_idx": 0, "source_anchor": r["vuid"],
            "condition": r["condition"], "core_version": r["entity_core_version"],
            "extensions": r["entity_extensions"], "refs": r["refs"],
            "index_text": index_text, "llm_text": llm_text,
        })

    # length stats (max over the three tokenizers) and the per-tokenizer max
    lengths = defaultdict(list)
    over = []
    for c in chunks:
        n = tokens.count_all(c["index_text"])
        c["n_tokens"] = n
        key = c["type"] if c["type"] == "vu" else f"section_{c['section_kind']}"
        lengths[key].append(max(n.values()))
        if max(n.values()) > max_tokens:
            over.append(c["chunk_id"])

    def pct(xs, q):
        xs = sorted(xs)
        return xs[min(len(xs) - 1, int(q * len(xs)))]

    length_stats = {k: {"n": len(v), "p50": pct(v, .5), "p90": pct(v, .9), "p99": pct(v, .99), "max": max(v)}
                    for k, v in lengths.items()}

    # coverage: every explicit VUID has a VU chunk and a parent section
    explicit = [r for r in recs if r["explicit"]]
    unmapped = [r["vuid"] for r in explicit if not r["section_id"]]
    html_ids = set(vuid_to_section)
    built = set(by_vuid)
    coverage = {
        "explicit_total": len(explicit),
        "explicit_with_section": len(explicit) - len(unmapped),
        "coverage": (len(explicit) - len(unmapped)) / len(explicit),
        "unmapped_explicit": unmapped[:200],
        "json_vuids_missing_in_html": sorted(built - html_ids)[:200],
        "html_vuids_missing_in_json": sorted(html_ids - built)[:200],
        "headers_diff": _headers_diff(cfg["spec"]["tag"], built),
        "sections": sec_stats,
        "chunks_by_type": Counter(c["type"] if c["type"] == "vu" else f"section_{c['section_kind']}" for c in chunks),
        "sections_split": sum(1 for c in chunks if c["type"] == "section" and c["part_idx"] == 1),
        "chunks_over_limit": over[:50],
        "vu_chunks_over_limit": {
            "explicit": sum(1 for c in chunks if c["type"] == "vu" and c["explicit"] and max(c["n_tokens"].values()) > max_tokens),
            "implicit": sum(1 for c in chunks if c["type"] == "vu" and not c["explicit"] and max(c["n_tokens"].values()) > max_tokens),
            "over_1024_xlmr": sum(1 for c in chunks if c["type"] == "vu" and c["n_tokens"]["xlmr"] > 1024),
        },
        "length_tokens_max_of_three": length_stats,
        "tokenizers": tokens.revisions(),
        "equivalence": eq_report,
        "refs_unresolved": None,
    }
    all_refs = Counter(ref for c in chunks for ref in c["refs"])
    unresolved = {a: n for a, n in all_refs.items() if a not in anchor_to_chunk and a not in by_vuid}
    coverage["refs_unresolved"] = {"distinct": len(unresolved), "total_distinct": len(all_refs),
                                   "top": Counter(unresolved).most_common(20)}

    PROCESSED.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with open(PROCESSED / "vuids.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            r = {k: v for k, v in r.items() if k != "text_html"}
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (PROCESSED / "anchor_map.json").write_text(json.dumps(anchor_to_chunk, indent=0, sort_keys=True), encoding="utf-8")
    corpus_hash = hashlib.sha256()
    for c in sorted(chunks, key=lambda c: c["chunk_id"]):
        corpus_hash.update((c["chunk_id"] + "\x00" + c["index_text"] + "\x00" + c["llm_text"] + "\n").encode("utf-8"))
    coverage["corpus_hash"] = corpus_hash.hexdigest()
    coverage["build_info"] = json.loads((BUILD / "build_info.json").read_text(encoding="utf-8"))
    (PROCESSED / "coverage_report.json").write_text(json.dumps(coverage, indent=1, default=dict), encoding="utf-8")
    return coverage
