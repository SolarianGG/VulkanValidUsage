"""Stage 2 input: gpuinfo.org extension coverage snapshot (PLAN §4 Stage 2, §9.1).

gpuinfo.org has no stable API, so the snapshot is a manual export: the user saves the page
`https://vulkan.gpuinfo.org/listextensions.php?platform=<os>` for each desktop platform
into `data/external/gpuinfo/<os>.html`. This module parses the saved pages into
`data/external/gpuinfo_snapshot.json`.

Metric: "Device coverage" column = share of devices (in the selected age window) that report
the extension. Instance extensions are on a separate page, `listinstanceextensions.php?platform=<os>`
(saved as `<os>_instance.html`; share of reports, no age filter). Values are fractions in [0, 1].

Combining platforms (`strata.gpuinfo_combine`):
  mean      plain mean over platforms (an extension missing on a platform counts as 0 there);
  platform  like `mean`, but an extension bound to a window system (vk.xml `platform` attribute,
            e.g. win32 / xlib / wayland) is rated only on the OS where it can exist (max over
            platforms), so `VK_KHR_win32_surface` is not halved by Linux.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from vkrag.config import EXTERNAL, PROCESSED, ROOT, load_config

PAGES_DIR = EXTERNAL / "gpuinfo"
SNAPSHOT = EXTERNAL / "gpuinfo_snapshot.json"

ROW_RE = re.compile(
    r'<tr role="row"[^>]*>\s*<td[^>]*>\s*(?:<a [^>]*>)?(?P<name>VK_[A-Za-z0-9_]+)(?:</a>)?\s*</td>'
    r'\s*<td[^>]*>\s*<a [^>]*>(?P<cov>[0-9.]+)<span[^>]*>%</span></a>\s*</td>'
    r'\s*<td[^>]*>\s*<a [^>]*>(?P<miss>[0-9.]+)<span[^>]*>%</span></a>\s*</td>'
    r'\s*<td[^>]*>(?P<first>[0-9-]*)</td>',
    re.S,
)
BODY_ROW_RE = re.compile(r'<tr role="row"[^>]*>\s*<td')
SAVED_FROM_RE = re.compile(r"saved from url=\(\d+\)(\S+)")
SELECTED_RE = re.compile(r'<select name="(?P<sel>[a-z]+)"[^>]*>(?P<body>.*?)</select>', re.S)
OPTION_SEL_RE = re.compile(r'<option value="(?P<v>[^"]*)" selected[^>]*>(?P<label>[^<]*)')
# vk.xml `platform` values that pin an extension to one desktop OS (others: no desktop OS at all)
PLATFORM_OS = {"win32": "windows", "xlib": "linux", "xlib_xrandr": "linux", "xcb": "linux", "wayland": "linux"}


def parse_page(text: str) -> dict:
    """One saved listextensions.php page -> {url, filters, coverage: {ext: fraction}, first_seen}."""
    m = SAVED_FROM_RE.search(text)
    url = m.group(1) if m else None
    filters = {}
    for s in SELECTED_RE.finditer(text):
        o = OPTION_SEL_RE.search(s.group("body"))
        if o:
            filters[s.group("sel")] = {"value": o.group("v"), "label": html.unescape(o.group("label")).strip()}
    cov, first = {}, {}
    for r in ROW_RE.finditer(text):
        name = r.group("name")
        c, miss = float(r.group("cov")), float(r.group("miss"))
        if abs(c + miss - 100.0) > 0.05:
            raise ValueError(f"{name}: coverage {c} + missing {miss} != 100")
        cov[name] = round(c / 100.0, 6)
        first[name] = r.group("first") or None
    n_rows = len(BODY_ROW_RE.findall(text))
    return {"url": url, "filters": filters, "coverage": cov, "first_seen": first, "table_rows": n_rows}


def combine(per_platform: dict[str, dict[str, float]], ext_platform: dict[str, str | None], how: str) -> dict[str, float]:
    platforms = sorted(per_platform)
    names = sorted(set().union(*(set(v) for v in per_platform.values())))
    out = {}
    for n in names:
        vals = [per_platform[p].get(n, 0.0) for p in platforms]
        if how == "platform" and ext_platform.get(n) in PLATFORM_OS:
            out[n] = max(vals)
        elif how in ("mean", "platform"):
            out[n] = sum(vals) / len(vals)
        elif how == "min":
            out[n] = min(vals)
        elif how == "max":
            out[n] = max(vals)
        else:
            raise ValueError(f"unknown combine rule {how!r}")
        out[n] = round(out[n], 6)
    return out


def run() -> dict:
    cfg = load_config()["strata"]
    platforms = cfg.get("gpuinfo_platforms", ["windows", "linux"])
    how = cfg.get("gpuinfo_combine", "platform")
    reg = json.loads((PROCESSED / "registry.json").read_text(encoding="utf-8"))
    ext_platform = {k: v.get("platform") for k, v in reg["extensions"].items()}
    pages, per_platform = {}, {}
    for p in platforms:
        per_platform[p] = {}
        for kind, suffix, page_name in (("device", "", "listextensions"), ("instance", "_instance", "listinstanceextensions")):
            path = PAGES_DIR / f"{p}{suffix}.html"
            if not path.exists():
                if kind == "device":
                    raise FileNotFoundError(path)
                continue
            page = parse_page(path.read_text(encoding="utf-8"))
            if page["url"] and (f"platform={p}" not in page["url"] or f"/{page_name}.php" not in page["url"]):
                raise ValueError(f"{path}: saved from {page['url']}, expected {page_name}.php?platform={p}")
            if len(page["coverage"]) != page["table_rows"]:
                raise ValueError(f"{path}: parsed {len(page['coverage'])} rows of {page['table_rows']}")
            clash = set(page["coverage"]) & set(per_platform[p])
            if clash:
                raise ValueError(f"{path}: extensions on both device and instance pages: {sorted(clash)[:5]}")
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()
            pages[f"{p}_{kind}"] = {"file": str(path.relative_to(ROOT)).replace("\\", "/"), "url": page["url"], "saved": mtime,
                                    "filters": page["filters"], "extensions": len(page["coverage"])}
            per_platform[p].update(page["coverage"])
    combined = combine(per_platform, ext_platform, how)
    in_registry = set(reg["extensions"])
    snap = {
        "date": max(v["saved"] for v in pages.values()),
        "source": "https://vulkan.gpuinfo.org/listextensions.php (saved pages)",
        "platforms": platforms,
        "window": {p: v["filters"].get("age", {}).get("label", "no age filter on page") for p, v in pages.items()},
        "metric": "device coverage: share of devices reporting the extension",
        "combine": how,
        "pages": pages,
        "unknown_to_registry": sorted(set(combined) - in_registry),
        "registry_missing_from_snapshot": len(in_registry - set(combined)),
        "per_platform": per_platform,
        "extensions": combined,
    }
    SNAPSHOT.write_text(json.dumps(snap, indent=1, sort_keys=True), encoding="utf-8")
    return snap


def sensitivity(threshold: float) -> dict[str, int]:
    """Number of extensions at or above the popularity threshold under each combine rule."""
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    reg = json.loads((PROCESSED / "registry.json").read_text(encoding="utf-8"))
    ext_platform = {k: v.get("platform") for k, v in reg["extensions"].items()}
    out = {}
    for how in ("min", "mean", "platform", "max"):
        c = combine(snap["per_platform"], ext_platform, how)
        out[how] = sum(1 for n, v in c.items() if v >= threshold and n.split("_")[1] in ("KHR", "EXT"))
    return out


if __name__ == "__main__":
    s = run()
    print(json.dumps({k: s[k] for k in ("date", "window", "combine", "pages", "unknown_to_registry", "registry_missing_from_snapshot")}, indent=1))
    print(Path(SNAPSHOT))
