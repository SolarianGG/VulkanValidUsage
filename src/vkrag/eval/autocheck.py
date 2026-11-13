"""Automatic answer checks without the judge (PLAN §7.2):
- vk identifiers (vk*/Vk*/VK_*/PFN_vk*) against the current registry + aliases: missing everywhere ->
  fabricated_identifier; present only in older tags -> outdated_identifier. Member and parameter names
  are not checked (camelCase words in prose are not reliably identifiers);
- cited VUIDs (with or without the `VUID-` prefix) against the current validusage: fabricated_vuid;
- citation accuracy: a cited VUID is in the gold class or a class of acceptable_vuids;
- yes/no verdict extraction: yes | no | conditional | none.
"""

from __future__ import annotations

import json
import re
from functools import cached_property

from vkrag.config import EXTERNAL, PROCESSED

VK_ID = re.compile(r"\b(?:PFN_vk|vk|Vk|VK_)[A-Za-z0-9_]+\b")
VUID_FULL = re.compile(r"\bVUID-([A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*-\d{5})\b")
VUID_BARE = re.compile(
    r"(?<![\w-])((?:vk|Vk|VK|Spv|Runtime|Standalone|Base|Builtin)[A-Za-z0-9_]*-[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*-\d{5})\b"
)
VERDICT = re.compile(r"^\W*(yes|no)\b", re.I)
CONDITIONAL = re.compile(r"^\W*(it depends|depends|only if|not necessarily|conditionally|it can be|sometimes)\b", re.I)


class Checker:
    @cached_property
    def current(self) -> set[str]:
        ids = json.load(open(PROCESSED / "identifiers.json", encoding="utf-8"))
        names: set[str] = set()
        for v in ids["by_kind"].values():
            names.update(v)
        al = json.load(open(PROCESSED / "aliases.json", encoding="utf-8"))
        names.update(al["alias_to_target"])
        names.update(al["alias_to_target"].values())
        names.update(l.strip() for l in open(EXTERNAL / "spirv_identifiers.txt", encoding="utf-8") if l.strip())
        return names

    @cached_property
    def outdated(self) -> set[str]:
        ids = json.load(open(PROCESSED / "identifiers.json", encoding="utf-8"))
        return set(ids["outdated"]) | set(ids["newer"])

    @cached_property
    def vu_class(self) -> dict[str, str]:
        out = {}
        for line in open(PROCESSED / "vuids.jsonl", encoding="utf-8"):
            v = json.loads(line)
            out[v["vuid"]] = v["equiv_class_id"]
        return out

    def identifiers(self, text: str, given: str = "") -> dict:
        """`given`: the question text; identifiers taken from it (e.g. the invented one of an
        unanswerable question) are not the answerer's fabrication."""
        fab, old = set(), set()
        in_question = {m.group(0) for m in VK_ID.finditer(given)}
        for m in VK_ID.finditer(text):
            t = m.group(0)
            if t in self.current or t in in_question or _is_vuid_part(text, m):
                continue
            (old if t in self.outdated else fab).add(t)
        return {
            "fabricated_identifiers": sorted(fab),
            "outdated_identifiers": sorted(old),
            "fabricated_identifier": bool(fab),
            "outdated_identifier": bool(old),
        }

    def cited_vuids(self, text: str) -> list[str]:
        out = ["VUID-" + m.group(1) for m in VUID_FULL.finditer(text)]
        stripped = VUID_FULL.sub(" ", text)
        out += ["VUID-" + m.group(1) for m in VUID_BARE.finditer(stripped)]
        return list(dict.fromkeys(out))

    def check(self, answer: str, q: dict) -> dict:
        res = self.identifiers(answer, q.get("question", ""))
        cited = self.cited_vuids(answer)
        fab_vu = [v for v in cited if v not in self.vu_class]
        res.update({"cited_vuids": cited, "fabricated_vuids": fab_vu, "fabricated_vuid": bool(fab_vu)})
        if q.get("vuid"):
            ok_cls = {self.vu_class[q["vuid"]]} | {self.vu_class[a] for a in q.get("acceptable_vuids") or [] if a in self.vu_class}
            real = [v for v in cited if v in self.vu_class]
            res["citation_correct"] = any(self.vu_class[v] in ok_cls for v in real) if cited else None
            res["citation_precision"] = (sum(self.vu_class[v] in ok_cls for v in real) / len(cited)) if cited else None
        if q.get("answer_type") == "yes_no":
            res["verdict"] = verdict(answer)
            res["verdict_match"] = res["verdict"] == q.get("expected_verdict")
        return res


def _is_vuid_part(text: str, m: re.Match) -> bool:
    """`vkCmdDraw` inside `VUID-vkCmdDraw-None-02700` or a bare `vkCmdDraw-None-02700` is not an identifier claim."""
    return text[max(0, m.start() - 5) : m.start()] == "VUID-" or text[m.end() : m.end() + 1] == "-"


def verdict(answer: str) -> str:
    a = re.sub(r"[*_`#>]", "", answer).strip()
    m = VERDICT.match(a)
    if m:
        return m.group(1).lower()
    return "conditional" if CONDITIONAL.match(a) else "none"
