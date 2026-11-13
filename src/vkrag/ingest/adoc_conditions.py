"""Extension condition for every explicit VUID, taken from the ifdef stack in the adoc source.

validusage.json (schema v2) gives every VU the condition `core` (data_facts.md), so this mini asciidoc
preprocessor replays what the `-spec all` build does:
  - walks include:: from vkspec.adoc with attribute substitution ({chapters}, {refpage}, ...);
  - {generated}/... is not walked (only prototypes and implicit validity live there; verified);
  - ifdef/ifndef are evaluated against gen/specattribs.adoc plus `:name:` lines in the text;
  - for included VUID anchors the condition is the DNF conjunction of all active ifdefs (ifndef is not
    recorded: under -spec all everything inside ifndef::VK_*[] is excluded, and ifndef::VKSC*/hidden is always true);
  - clauses with atoms undefined in this build are false and dropped; defined non-VK_* atoms
    (service attributes) are removed from clauses.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from vkrag.conditions import DNF, conj_all, is_mixed, minimize, parse_ifdef, simplify_versions, to_str
from vkrag.config import BUILD, PROCESSED, RAW

DOCS = RAW / "Vulkan-Docs"

RE_IFDEF = re.compile(r"^(ifdef|ifndef)::([^\[]+)\[(.*)\]\s*$")
RE_ENDIF = re.compile(r"^endif::([^\[]*)\[\]\s*$")
RE_ATTR_SET = re.compile(r"^:(!?)([\w-]+?)(!?):(?:\s+(.*))?$")
RE_INCLUDE = re.compile(r"^include::([^\[]+)\[(.*)\]\s*$")
RE_TAGOPT = re.compile(r"tags?=([^,\]]+)")
RE_VUID = re.compile(r"\[\[(VUID-[^\]]+)\]\]")
RE_ATTRREF = re.compile(r"\{([\w-]+)\}")
RE_REFPAGE = re.compile(r"^\[open,refpage='([^']+)'")


@dataclass
class Found:
    conds: list[DNF] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    refpage: str | None = None


class Preprocessor:
    def __init__(self, defined: set[str], attrs: dict[str, str]):
        self.defined = set(defined)
        self.attrs = dict(attrs)
        self.found: dict[str, Found] = defaultdict(Found)
        self.stats = Counter()
        self.unresolved: list[str] = []
        self.mixed: list[str] = []

    def sub(self, s: str) -> str:
        for _ in range(5):
            n = RE_ATTRREF.sub(lambda m: self.attrs.get(m.group(1), m.group(0)), s)
            if n == s:
                break
            s = n
        return s

    def is_defined(self, name: str) -> bool:
        return name in self.defined or name in self.attrs

    def evaluate(self, kind: str, expr: str) -> bool:
        """Stock asciidoctor semantics (what actually ends up in the build)."""
        if "," in expr:
            ok = any(self.is_defined(a.strip()) for a in expr.split(","))
        else:
            ok = all(self.is_defined(a.strip()) for a in expr.split("+"))
        return ok if kind == "ifdef" else not ok

    def restrict(self, d: DNF) -> DNF | None:
        """Keep clauses that are true in this build, and only VK_* atoms. None means the condition is always false."""
        out = []
        for cl in d:
            if not all(self.is_defined(a) for a in cl):
                continue
            out.append(frozenset(a for a in cl if a.startswith("VK")))
        if not out:
            return None
        return minimize(frozenset(out))

    def run(self, path: Path) -> None:
        self._file(path, [], 0)

    def _file(self, path: Path, stack: list[DNF], depth: int, tags: list[str] | None = None) -> None:
        if depth > 30:
            raise RecursionError(path)
        self.stats["files"] += 1
        rel = path.relative_to(DOCS).as_posix()
        # per-file condition stack: (included?, DNF or None)
        local: list[tuple[bool, DNF | None]] = []
        skip_depth = 0  # >0: inside an excluded region
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
        numbered = list(enumerate(lines, 1))
        if tags:
            numbered = self._tagged(numbered, tags)
            if not numbered:
                self.unresolved.append(f"{rel}: tags {tags} not found")
        for lineno, line in numbered:
            m = RE_IFDEF.match(line)
            if m and m.group(3) == "":
                kind, expr = m.group(1), m.group(2)
                if skip_depth:
                    skip_depth += 1
                    continue
                if not self.evaluate(kind, expr):
                    skip_depth = 1
                    continue
                d = None
                if kind == "ifdef":
                    if is_mixed(expr):
                        self.mixed.append(f"{rel}:{lineno}: {expr}")
                    d = self.restrict(parse_ifdef(expr))
                local.append((True, d))
                continue
            if RE_ENDIF.match(line):
                if skip_depth:
                    skip_depth -= 1
                elif local:
                    local.pop()
                else:
                    self.stats["unbalanced_endif"] += 1
                continue
            if skip_depth:
                continue
            m = RE_ATTR_SET.match(line)
            if m:
                neg = m.group(1) or m.group(3)
                name = m.group(2)
                if neg:
                    self.attrs.pop(name, None)
                else:
                    self.attrs[name] = self.sub(m.group(4) or "")
                continue
            m = RE_INCLUDE.match(line)
            if m:
                target = self.sub(m.group(1).strip())
                if "{" in target:
                    self.unresolved.append(f"{rel}:{lineno}: {target}")
                    continue
                if target.startswith(self.attrs["generated"]):
                    self.stats["include_generated_skipped"] += 1
                    continue
                p = Path(target)
                if not p.is_absolute():
                    p = (path.parent / p).resolve()
                if not p.exists():
                    self.unresolved.append(f"{rel}:{lineno}: missing {target}")
                    continue
                cur = stack + [d for _, d in local if d is not None]
                tm = RE_TAGOPT.search(m.group(2))
                tags = [t.strip() for t in tm.group(1).split(";")] if tm else None
                self._file(p, cur, depth + 1, tags)
                continue
            for vm in RE_VUID.finditer(line):
                vuid = self.sub(vm.group(1))
                if "{" in vuid:
                    self.unresolved.append(f"{rel}:{lineno}: {vuid}")
                    continue
                cond = conj_all(stack + [d for _, d in local if d is not None])
                fd = self.found[vuid]
                fd.conds.append(cond)
                fd.sources.append(f"{rel}:{lineno}")
                fd.refpage = fd.refpage or self.attrs.get("refpage")
                self.stats["vuid_anchors"] += 1
        if local or skip_depth:
            self.stats["unclosed_ifdef_files"] += 1

    @staticmethod
    def _tagged(numbered: list[tuple[int, str]], tags: list[str]) -> list[tuple[int, str]]:
        """Lines between `tag::NAME[]` and `end::NAME[]` (markers usually live in comments `// tag::x[]`)."""
        out, active = [], set()
        for n, line in numbered:
            mt = re.search(r"tag::([\w-]+)\[\]", line)
            me = re.search(r"end::([\w-]+)\[\]", line)
            if mt and mt.group(1) in tags:
                active.add(mt.group(1))
                continue
            if me and me.group(1) in active:
                active.discard(me.group(1))
                continue
            if active and not (mt or me):
                out.append((n, line))
        return out


def defined_attributes() -> set[str]:
    text = (BUILD / "specattribs.adoc").read_text(encoding="utf-8")
    return {m.group(1) for m in re.finditer(r"^:([\w-]+):", text, re.M)}


def run() -> dict:
    attrs = {
        "chapters": str(DOCS / "chapters"),
        "appendices": str(DOCS / "appendices"),
        "config": str(DOCS / "config"),
        "generated": str(DOCS / "gen"),
        "promoted": str(DOCS / "gen" / "promoted"),
        "images": str(DOCS / "images"),
        "proposals": str(DOCS / "proposals"),
    }
    pp = Preprocessor(defined_attributes(), attrs)
    pp.run(DOCS / "vkspec.adoc")
    out = {}
    multi = 0
    for vuid, fd in pp.found.items():
        cond = fd.conds[0]
        if len(fd.conds) > 1:
            multi += 1
            # the same VUID at several sites: OR of the conditions
            cond = minimize(frozenset().union(*fd.conds))
        out[vuid] = {
            "condition": to_str(simplify_versions(cond)),
            "condition_raw": to_str(cond),
            "sources": fd.sources,
            "refpage": fd.refpage,
        }
    report = {
        "vuids": len(out),
        "multi_site_vuids": multi,
        "stats": dict(pp.stats),
        "unresolved": pp.unresolved[:200],
        "unresolved_count": len(pp.unresolved),
        "mixed_expressions": pp.mixed,
        "condition_values": Counter(v["condition"] for v in out.values()).most_common(15),
    }
    PROCESSED.mkdir(parents=True, exist_ok=True)
    (PROCESSED / "vu_conditions.json").write_text(json.dumps(out, indent=0, sort_keys=True), encoding="utf-8")
    return report
