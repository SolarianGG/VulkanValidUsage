"""Extension conditions of VUs in DNF.

Data fact (reports/data_facts.md): in validusage.json schema v2 the condition is always `core`,
because ifdefs are resolved at build time. The VU condition is therefore reconstructed from the
`ifdef::` stack in the adoc source (see ingest/adoc_conditions.py); this module is the algebra over it.

asciidoctor semantics: `ifdef::a,b[]` is OR, `ifdef::a+b[]` is AND; no parentheses and no mixing
(if `,` is present the string is split on `,`). Nested ifdefs combine with AND.
DNF = frozenset of clauses; clause = frozenset of names (AND). The empty clause = `core` (unconditional).
"""

from __future__ import annotations

import re
from collections.abc import Iterable

Clause = frozenset[str]
DNF = frozenset[Clause]

CORE: DNF = frozenset({frozenset()})
VERSION_RE = re.compile(r"^VK_(?:(?:BASE|COMPUTE|GRAPHICS)_)?VERSION_(\d+)_(\d+)$")


def parse_ifdef(expr: str) -> DNF:
    """A single ifdef expression -> DNF."""
    expr = expr.strip()
    if not expr:
        raise ValueError("empty ifdef expression")
    # The mixed form `A,B+C` occurs once in the spec; it is read as A OR (B AND C)
    # (the authors' intent; stock asciidoctor would read `B+C` as one name). See data_facts.md.
    clauses = []
    for part in expr.split(","):
        atoms = [a.strip() for a in part.split("+")]
        if any(not a for a in atoms):
            raise ValueError(f"bad ifdef expression: {expr!r}")
        clauses.append(frozenset(atoms))
    return minimize(frozenset(clauses))


def is_mixed(expr: str) -> bool:
    return "," in expr and "+" in expr


def conj(a: DNF, b: DNF) -> DNF:
    return minimize(frozenset(x | y for x in a for y in b))


def conj_all(items: Iterable[DNF]) -> DNF:
    res = CORE
    for it in items:
        res = conj(res, it)
    return res


def minimize(d: DNF) -> DNF:
    """Absorption: a clause that is a superset of another clause is redundant."""
    cl = sorted(d, key=len)
    keep: list[Clause] = []
    for c in cl:
        if not any(k <= c for k in keep):
            keep.append(c)
    return frozenset(keep)


def version_of(name: str) -> tuple[int, int] | None:
    m = VERSION_RE.match(name)
    return (int(m.group(1)), int(m.group(2))) if m else None


def simplify_versions(d: DNF) -> DNF:
    """Within a clause, all VK_{,BASE_,COMPUTE_,GRAPHICS_}VERSION_x_y collapse to one VK_VERSION_<max>.
    VK_VERSION_1_0 next to extensions is always true in Vulkan and is dropped."""
    out = []
    for cl in d:
        vers = [v for v in (version_of(a) for a in cl) if v]
        rest = {a for a in cl if not version_of(a)}
        if vers:
            mx = max(vers)
            if not (rest and mx == (1, 0)):
                rest.add(f"VK_VERSION_{mx[0]}_{mx[1]}")
        out.append(frozenset(rest))
    return minimize(frozenset(out))


def to_str(d: DNF) -> str:
    if d == CORE:
        return "core"
    return ",".join(sorted("+".join(sorted(c)) for c in d))


def from_str(s: str) -> DNF:
    """Inverse of to_str (storage format in vuids.jsonl): `,` is OR of clauses, `+` is AND within a clause."""
    if s == "core":
        return CORE
    return frozenset(frozenset(c.split("+")) for c in s.split(","))
