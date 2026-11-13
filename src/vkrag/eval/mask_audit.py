"""Audit of the answer masking: residual configuration markers after mask() (PLAN §7.2 blinding).

Run: uv run python -m vkrag.eval.mask_audit [run_id]
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter

from vkrag.config import ROOT
from vkrag.eval.masking import mask

RESIDUAL = re.compile(r"\b(context|provided|snippet|excerpt|passage|retriev\w*|own knowledge)\b|\[\d+\]", re.I)


def main(run_id: str = "pilot") -> None:
    by_cfg, hits, n = Counter(), Counter(), Counter()
    examples = []
    for line in open(ROOT / "runs" / run_id / "answers.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r["missing"]:
            continue
        t, marker = mask(r["answer"])
        n[r["config"]] += 1
        by_cfg[r["config"]] += marker
        for m in RESIDUAL.finditer(t):
            hits[r["config"]] += 1
            if len(examples) < 25:
                examples.append((r["config"], t[max(0, m.start() - 60) : m.end() + 40].replace("\n", " ")))
            break
    print("config | answers | marker removed | residual")
    for c in n:
        print(c, n[c], by_cfg[c], hits[c])
    for c, e in examples:
        print(f"[{c}] ...{e}...")


if __name__ == "__main__":
    main(*sys.argv[1:])
