"""Stage 2: dating of explicit VUs over historical tags -> data/processed/vuid_history.json.

Date of a VU = date of the first Vulkan-Docs tag whose validusage.json contains a VUID with the
same numeric suffix (PLAN §4 Stage 2). The full VUID string is not used: promotion and parameter
renames change it (`VUID-vkCmdBeginRenderingKHR-...` -> `VUID-vkCmdBeginRendering-...`).

Historical validusage.json comes from Vulkan-Headers `registry/validusage.json` of the same tag
(PLAN §9.2 item 1); tag dates come from Vulkan-Docs. Only tags released within
`strata.history_years` before the freeze date are scanned, plus one baseline tag before the
window: a suffix already present in the baseline is "before_window" (old by construction).

`text_changed_recently` (PLAN §4 Stage 2): the normalized text of the VU at the current tag vs.
`strata.text_change.last_n_tags` tags back: normalized Levenshtein distance above the threshold,
or a changed set of identifiers.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import deque
from datetime import date, timedelta

from rapidfuzz.distance import Levenshtein
from tqdm import tqdm

from vkrag.config import PROCESSED, RAW, load_config
from vkrag.normalize import html_to_text

DOCS = RAW / "Vulkan-Docs"
HEADERS = RAW / "Vulkan-Headers"
TAG_RE = re.compile(r"^v1\.(\d+)\.(\d+)$")
# Vulkan / SPIR-V style identifiers: vk/Vk/VK_ prefixes, multi-word camelCase, SNAKE_CASE
IDENT_RE = re.compile(
    r"\b(?:vk[A-Z]\w*|Vk[A-Z]\w*|VK_\w+|[a-z]+(?:[A-Z][a-z0-9]*)+|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+|[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b"
)


def tag_key(t: str) -> tuple[int, int]:
    m = TAG_RE.match(t)
    assert m, t
    return int(m.group(1)), int(m.group(2))


def docs_tag_dates() -> dict[str, str]:
    out = subprocess.run(
        ["git", "-C", str(DOCS), "for-each-ref", "--format=%(refname:short) %(creatordate:short)", "refs/tags/v1.*"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    res = {}
    for line in out.splitlines():
        t, d = line.split()
        if TAG_RE.match(t):
            res[t] = d
    return res


def select_tags(dates: dict[str, str], current: str, freeze: date, years: int) -> tuple[list[str], str]:
    """Tags <= current released within `years` before the freeze date, plus the baseline tag before them."""
    start = (freeze - timedelta(days=round(365.25 * years))).isoformat()
    tags = sorted((t for t in dates if tag_key(t) <= tag_key(current)), key=tag_key)
    inside = [t for t in tags if dates[t] >= start]
    before = [t for t in tags if dates[t] < start]
    if not before:
        raise ValueError("no baseline tag before the history window")
    return [before[-1]] + inside, start


def headers_validusage(tag: str) -> dict | None:
    r = subprocess.run(["git", "-C", str(HEADERS), "show", f"{tag}:registry/validusage.json"], capture_output=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def iter_vus(vu: dict):
    for entity, by_cond in vu["validation"].items():
        for lst in by_cond.values():
            for e in lst:
                yield entity, e["vuid"], e["text"]


def suffix_of(vuid: str) -> str:
    return vuid.rsplit("-", 1)[-1]


def normalize_for_diff(text: str) -> str:
    return " ".join(text.split())


def identifier_set(text: str) -> frozenset[str]:
    return frozenset(IDENT_RE.findall(text))


def text_change(old: str, new: str, threshold: float) -> dict:
    a, b = normalize_for_diff(old), normalize_for_diff(new)
    dist = Levenshtein.normalized_distance(a, b)
    ia, ib = identifier_set(a), identifier_set(b)
    return {
        "lev": round(dist, 4),
        "ids_added": sorted(ib - ia),
        "ids_removed": sorted(ia - ib),
        "changed": dist > threshold or ia != ib,
    }


def run() -> dict:
    cfg = load_config()
    current = cfg["spec"]["tag"]
    freeze = date.fromisoformat(cfg["spec"]["freeze_date"])
    st = cfg["strata"]
    dates = docs_tag_dates()
    tags, window_start = select_tags(dates, current, freeze, st["history_years"])
    last_n = st["text_change"]["last_n_tags"]
    lev_thr = st["text_change"]["levenshtein"]

    first_seen: dict[str, str] = {}  # numeric suffix -> first tag
    skipped: list[str] = []
    scanned: list[str] = []
    # rolling window: explicit VU texts of the last `last_n + 1` scanned tags (current is the last tag)
    window: deque[tuple[str, dict[str, tuple[str, str]]]] = deque(maxlen=last_n + 1)
    for t in tqdm(tags, desc="tags"):
        vu = headers_validusage(t)
        if vu is None:
            skipped.append(t)
            continue
        scanned.append(t)
        texts = {}
        for entity, vuid, text in iter_vus(vu):
            s = suffix_of(vuid)
            if s.isdigit():
                texts[vuid] = (entity, text)
                if s not in first_seen:
                    first_seen[s] = t
        window.append((t, texts))
    if not scanned or scanned[-1] != current:
        raise ValueError(f"current tag {current} has no Headers validusage.json")
    old_tag, old = window[0]
    cur = window[-1][1]

    aliases = json.loads((PROCESSED / "aliases.json").read_text(encoding="utf-8"))["alias_to_target"]
    canon = lambda n: aliases.get(n, n)  # noqa: E731
    old_by_suffix: dict[str, list[str]] = {}
    for vuid in old:
        old_by_suffix.setdefault(suffix_of(vuid), []).append(vuid)

    cache: dict[str, str] = {}

    def norm(raw: str) -> str:
        if raw not in cache:
            cache[raw] = html_to_text(raw)[0]
        return cache[raw]

    baseline = scanned[0]
    records: dict[str, dict] = {}
    stats = {
        "explicit": 0,
        "before_window": 0,
        "dated_in_window": 0,
        "undated": 0,
        "new_in_last_n": 0,
        "text_changed_recently": 0,
        "matched_old_by": {},
    }
    for vuid, (entity, raw) in sorted(cur.items()):
        s = suffix_of(vuid)
        stats["explicit"] += 1
        ft = first_seen.get(s)
        rec = {"suffix": s, "first_tag": ft, "first_date": dates.get(ft) if ft else None, "before_window": ft == baseline}
        if ft is None:
            stats["undated"] += 1
        elif ft == baseline:
            stats["before_window"] += 1
        else:
            stats["dated_in_window"] += 1
        # text-change check against `old_tag`
        how = None
        if vuid in old:
            match = vuid
            how = "vuid"
        else:
            cands = old_by_suffix.get(s, [])
            same_entity = [c for c in cands if canon(old[c][0]) == canon(entity)]
            if same_entity:
                match, how = same_entity[0], "suffix+entity"
            elif cands:
                match = min(cands, key=lambda c: Levenshtein.normalized_distance(norm(old[c][1]), norm(raw)))
                how = "suffix_closest"
            else:
                match = None
        if match is None:
            rec["new_in_last_n"] = True
            rec["text_changed_recently"] = False
            stats["new_in_last_n"] += 1
        else:
            stats["matched_old_by"][how] = stats["matched_old_by"].get(how, 0) + 1
            rec["new_in_last_n"] = False
            if old[match][1] == raw:
                rec["text_changed_recently"] = False
            else:
                ch = text_change(norm(old[match][1]), norm(raw), lev_thr)
                rec["text_changed_recently"] = ch["changed"]
                rec["text_change"] = {"old_vuid": match, **ch}
            stats["text_changed_recently"] += rec["text_changed_recently"]
        records[vuid] = rec

    # sanity check of the "numeric suffixes grow monotonically" proxy (outliers are expected)
    order = {t: i for i, t in enumerate(scanned)}
    dated = [(int(r["suffix"]), order[r["first_tag"]]) for r in records.values() if r["first_tag"] and not r["before_window"]]
    monotonic = None
    if len(dated) > 10:
        from scipy.stats import spearmanr

        rho = spearmanr([a for a, _ in dated], [b for _, b in dated]).statistic
        base_max = max((int(r["suffix"]) for r in records.values() if r["before_window"]), default=0)
        below = sum(1 for a, _ in dated if a < base_max)
        monotonic = {
            "spearman_suffix_vs_tag": round(float(rho), 4),
            "max_suffix_before_window": base_max,
            "dated_with_suffix_below_that": below,
        }

    per_tag: dict[str, int] = {}
    for r in records.values():
        if r["first_tag"] and not r["before_window"]:
            per_tag[r["first_tag"]] = per_tag.get(r["first_tag"], 0) + 1
    out = {
        "current_tag": current,
        "window_start": window_start,
        "baseline_tag": baseline,
        "text_change_old_tag": old_tag,
        "text_change_params": st["text_change"],
        "tags": {t: dates[t] for t in tags},
        "tags_scanned": len(scanned),
        "tags_skipped": skipped,
        "stats": stats,
        "monotonic_check": monotonic,
        "new_vus_per_tag": {t: per_tag.get(t, 0) for t in scanned[1:]},
        "vuids": records,
    }
    (PROCESSED / "vuid_history.json").write_text(json.dumps(out, indent=0, sort_keys=False), encoding="utf-8")
    return out
