"""Stage 1, item 9: equivalence classes of VUs.

- main rule: explicit VUIDs with the same numeric suffix form a class (mostly `commonvalidity`
  templates shared by draw/dispatch/trace-rays/copy commands);
- additionally, explicit VUs whose normalized text is *exactly* equal after replacing the entity
  name (and its aliases) with a placeholder are merged. No fuzzy matching;
- implicit VUs are never merged (each is its own class), otherwise template rules such as
  "must be a valid handle" would collapse into huge classes.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict


class _DSU:
    def __init__(self) -> None:
        self.p: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # deterministic root: lexicographically smallest
            if rb < ra:
                ra, rb = rb, ra
            self.p[rb] = ra


def text_key(rec: dict, alias_names: dict[str, list[str]], placeholder: bool = True) -> str:
    t = rec["text"]
    if not placeholder:
        return re.sub(r"\s+", " ", t).strip().lower()
    names = {rec["entity"], rec["vuid_entity"], *alias_names.get(rec["entity"], [])}
    for n in sorted(names, key=len, reverse=True):
        t = re.sub(rf"\b{re.escape(n)}\b", "<ENTITY>", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def assign_classes(recs: list[dict], alias_names: dict[str, list[str]], placeholder: bool = True) -> dict:
    dsu = _DSU()
    by_suffix: dict[int, list[str]] = defaultdict(list)
    by_text: dict[str, list[str]] = defaultdict(list)
    for r in recs:
        dsu.find(r["vuid"])
        if not r["explicit"]:
            continue
        by_suffix[r["suffix_num"]].append(r["vuid"])
        by_text[text_key(r, alias_names, placeholder)].append(r["vuid"])
    merged_by_text = 0
    merged_by_text_kind: Counter = Counter()
    kind = {r["vuid"]: r["entity_kind"] for r in recs}
    for group in by_suffix.values():
        for v in group[1:]:
            dsu.union(group[0], v)
    for group in by_text.values():
        for v in group[1:]:
            if dsu.find(group[0]) != dsu.find(v):
                merged_by_text += 1
                merged_by_text_kind[kind[v]] += 1
            dsu.union(group[0], v)
    members: dict[str, list[str]] = defaultdict(list)
    for r in recs:
        members[dsu.find(r["vuid"])].append(r["vuid"])
    class_id = {}
    for root, vs in members.items():
        cid = "eq-" + root.removeprefix("VUID-")
        for v in vs:
            class_id[v] = cid
    for r in recs:
        r["equiv_class_id"] = class_id[r["vuid"]]
        r["equiv_class_size"] = len(members[dsu.find(r["vuid"])])
    sizes = Counter(len(v) for root, v in members.items() if any(x.rsplit("-", 1)[-1].isdigit() for x in v))
    largest = sorted(((len(v), root) for root, v in members.items()), reverse=True)[:10]
    return {
        "explicit_classes": sum(sizes.values()),
        "size_distribution": dict(sorted(sizes.items())),
        "merged_by_text_only": merged_by_text,
        "merged_by_text_by_entity_kind": dict(merged_by_text_kind),
        "largest": [
            {"class": "eq-" + r.removeprefix("VUID-"), "size": n, "entities": sorted({m.split("-")[1] for m in members[r]})[:12]}
            for n, r in largest
        ],
    }
