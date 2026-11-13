"""Loading of configs/default.yaml and project paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else ROOT / "configs" / "default.yaml"
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config_value(dotted_key: str, value: Any, path: str | Path | None = None) -> None:
    """Update a single YAML value in place, keeping the rest of the file text intact."""
    import re

    p = Path(path) if path else ROOT / "configs" / "default.yaml"
    text = p.read_text(encoding="utf-8")
    leaf = dotted_key.split(".")[-1]
    # replace the first `leaf: <value>` occurrence inside the parent block
    parent = dotted_key.split(".")[0]
    start = text.index(f"\n{parent}:") if f"\n{parent}:" in text else 0
    pat = re.compile(rf"(^\s*{re.escape(leaf)}:\s*)([^#\n]*?)(\s*(#.*)?)$", re.M)
    m = pat.search(text, start)
    if not m:
        raise KeyError(dotted_key)
    rendered = yaml.safe_dump(value, default_flow_style=True).strip().removesuffix("...").strip()
    text = text[: m.start(2)] + rendered + text[m.end(2) :]
    p.write_text(text, encoding="utf-8")


DATA = ROOT / "data"
RAW = DATA / "raw"
BUILD = DATA / "build"
PROCESSED = DATA / "processed"
EXTERNAL = DATA / "external"
