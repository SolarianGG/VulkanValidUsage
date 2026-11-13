"""Stage 1 checkpoint helper: random chunks of every type and the largest equivalence classes,
written to reports/stage1_samples.md for manual review."""

from __future__ import annotations

import json
import random
from collections import defaultdict

from vkrag.config import PROCESSED, ROOT, load_config


def run(n: int = 10) -> str:
    seed = load_config()["seed"]
    chunks = [json.loads(l) for l in open(PROCESSED / "chunks.jsonl", encoding="utf-8")]
    recs = [json.loads(l) for l in open(PROCESSED / "vuids.jsonl", encoding="utf-8")]
    groups = defaultdict(list)
    for c in chunks:
        if c["type"] == "vu":
            groups["vu_explicit" if c["explicit"] else "vu_implicit"].append(c)
        else:
            groups[f"section_{c['section_kind']}" + ("_split" if c["n_parts"] > 1 else "")].append(c)
    out = ["# Stage 1 samples (manual review)", "", f"seed={seed}; token counts are max over qwen / xlmr / remote.", ""]
    for name in sorted(groups):
        rng = random.Random(f"{seed}-{name}")
        out += [f"## {name} ({len(groups[name])} chunks)", ""]
        for c in rng.sample(sorted(groups[name], key=lambda c: c["chunk_id"]), min(n, len(groups[name]))):
            meta = {
                k: c.get(k) for k in ("chunk_id", "entity", "section_id", "part_idx", "equiv_class_id", "condition") if c.get(k) is not None
            }
            out += [
                f"### `{c['chunk_id']}` ({max(c['n_tokens'].values())} tok)",
                "",
                "```",
                json.dumps(meta, ensure_ascii=False),
                "---",
                c["llm_text"][:2500],
                "```",
                "",
            ]
    by_cls = defaultdict(list)
    for r in recs:
        by_cls[r["equiv_class_id"]].append(r)
    largest = sorted(by_cls.values(), key=len, reverse=True)[:10]
    out += ["## 10 largest equivalence classes", ""]
    for members in largest:
        suffixes = sorted({m["suffix_num"] for m in members})
        texts = sorted({m["text"] for m in members})
        out += [
            f"### `{members[0]['equiv_class_id']}`: {len(members)} VUs, {len(suffixes)} distinct suffixes, {len(texts)} distinct texts",
            "",
            "Entities: " + ", ".join(sorted({m["entity"] for m in members})),
            "",
            "```",
        ]
        out += [t[:400] for t in texts[:3]] + ["```", ""]
    path = ROOT / "reports" / "stage1_samples.md"
    path.write_text("\n".join(out), encoding="utf-8")
    return str(path)


if __name__ == "__main__":
    print(run())
