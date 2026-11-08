"""Stage 1, item 6: the built single-page HTML -> section units (before length splitting).

Layout facts (reports/data_facts.md):
- every VU anchor sits inside a `Valid Usage` / `Valid Usage (Implicit)` sidebarblock, inside exactly
  one top-level `div.openblock` (a refpage block: command, structure, enum, built-in, ...);
- the entity anchor is a `div.listingblock id=<entity>` inside that openblock.

Units:
- `refpage`: one top-level openblock (parent is sectionbody/sectN) with the VU blocks removed.
  Short descriptive text (<= ATTACH_MAX_WORDS) right before the openblock is attached to it.
- `prose`: everything else directly inside a section (sect1..sect5), in document order, without
  child sections and refpage blocks.
VU blocks are removed from the tree before text extraction; their VUIDs go to `vuids_in_section`.
Host Synchronization and Command Properties stay in the text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag

from vkrag.config import BUILD
from vkrag.normalize import html_to_text

ATTACH_MAX_WORDS = 150
SECT_RE = re.compile(r"^sect(\d)$")
# "Chapter 21. Drawing Commands", "21.3. Programmable ...", "Appendix E: Layers & Extensions"
HEADING_NUM_RE = re.compile(r"^(?:(?:Chapter|Appendix)\s+)?(?:[A-Z](?=[.:\s])|\d+)(?:\.\d+)*[.:]?\s+")


@dataclass
class Unit:
    kind: str                     # refpage | prose
    source_anchor: str
    title: str
    path: list[str]               # titles of enclosing sections (chapter first)
    section_anchor: str           # id of the enclosing sectN heading
    elements: list[Tag] = field(default_factory=list)
    entity: str | None = None
    vuids_in_section: list[str] = field(default_factory=list)
    text: str = ""
    refs: list[str] = field(default_factory=list)
    anchors: list[str] = field(default_factory=list)


def _cls(el) -> list[str]:
    return el.get("class", []) if isinstance(el, Tag) else []


def _sect_level(el) -> int | None:
    for c in _cls(el):
        m = SECT_RE.match(c)
        if m:
            return int(m.group(1))
    return None


def _heading(sect: Tag) -> Tag | None:
    lvl = _sect_level(sect)
    return sect.find(f"h{lvl + 1}", recursive=False) if lvl is not None else None


def _clean_title(t: str) -> str:
    t = re.sub(r"\s+", " ", t).strip()
    return HEADING_NUM_RE.sub("", t, count=1).strip() or t


def _is_vu_block(el: Tag) -> bool:
    if el.name != "div" or "sidebarblock" not in _cls(el):
        return False
    title = el.select_one(":scope > .content > .title")
    return title is not None and title.get_text().strip().startswith("Valid Usage")


class SectionParser:
    def __init__(self, html: str, entities: set[str]):
        self.soup = BeautifulSoup(html, "lxml")
        self.entities = entities
        self.units: list[Unit] = []
        self.vu_block_vuids: dict[int, list[str]] = {}  # id(openblock) -> VUIDs
        self.stats = {"vu_blocks": 0, "vu_blocks_outside_refpage": 0}
        self.heading_fallback: dict[str, str] = {}  # heading id -> source_anchor of a unit

    def _strip_vu_blocks(self) -> None:
        for sb in list(self.soup.find_all("div", class_="sidebarblock")):
            if not _is_vu_block(sb):
                continue
            self.stats["vu_blocks"] += 1
            vuids = [a["id"] for a in sb.find_all("a", id=re.compile(r"^VUID-"))]
            ob = sb.find_parent("div", class_="openblock")
            if ob is None:
                self.stats["vu_blocks_outside_refpage"] += 1
            else:
                self.vu_block_vuids.setdefault(id(ob), []).extend(vuids)
            sb.decompose()

    def _is_refpage(self, el) -> bool:
        return isinstance(el, Tag) and el.name == "div" and "openblock" in _cls(el)

    def _refpage_identity(self, ob: Tag, vuids: list[str]) -> tuple[str | None, str | None]:
        anchor, entity = None, None
        for el in ob.find_all(id=True):
            if el.name == "div" and "listingblock" in _cls(el):
                anchor = el["id"]
                if el["id"] in self.entities:
                    entity = el["id"]
                break
        if anchor is None:
            first = ob.find(id=True)
            anchor = first["id"] if first is not None else None
        if entity is None and vuids:
            # built-ins and SPIR-V environments: entity from the VUID name
            names = [v.split("-")[1] for v in vuids]
            entity = max(set(names), key=names.count)
            anchor = anchor or entity
        return anchor, entity

    def parse(self) -> list[Unit]:
        self._strip_vu_blocks()
        content = self.soup.find(id="content")
        for s1 in content.find_all("div", class_="sect1", recursive=False):
            self._visit(s1, [])
        return self.units

    def _visit(self, sect: Tag, path: list[str]) -> None:
        h = _heading(sect)
        title = _clean_title(h.get_text()) if h is not None else "?"
        anchor = h.get("id") if h is not None else None
        container = sect.find("div", class_="sectionbody", recursive=False) if _sect_level(sect) == 1 else sect
        if container is None:
            return
        cur_path = path + [title]
        first_unit_idx = len(self.units)
        prose = Unit("prose", anchor or f"{'/'.join(cur_path)}", title, path, anchor or "")
        run: list[Tag] = []
        children_sects: list[Tag] = []
        rp_idx = 0
        for ch in container.children:
            if not isinstance(ch, Tag) or ch is h:
                continue
            if _sect_level(ch) is not None and ch.name == "div" and "sectionbody" not in _cls(ch):
                children_sects.append(ch)
                continue
            if self._is_refpage(ch):
                vuids = self.vu_block_vuids.get(id(ch), [])
                ra, ent = self._refpage_identity(ch, vuids)
                rp_idx += 1
                unit = Unit("refpage", ra or f"{anchor}#refpage{rp_idx}", ent or ra or title, cur_path, anchor or "",
                            entity=ent, vuids_in_section=vuids)
                words = sum(len(e.get_text().split()) for e in run)
                if run and words <= ATTACH_MAX_WORDS:
                    unit.elements.extend(run)
                else:
                    prose.elements.extend(run)
                run = []
                unit.elements.append(ch)
                self.units.append(unit)
                continue
            run.append(ch)
        prose.elements.extend(run)
        if prose.elements:
            self.units.append(prose)
        for cs in children_sects:
            self._visit(cs, cur_path)
        if not prose.elements and anchor and len(self.units) > first_unit_idx:
            # heading without own text: links to it resolve to the first unit inside the section
            self.heading_fallback[anchor] = self.units[first_unit_idx].source_anchor


def finalize(u: Unit) -> Unit:
    texts, refs, anchors = [], [], []
    for el in u.elements:
        t, r = html_to_text(el)
        if t:
            texts.append(t)
        refs.extend(r)
        if el.get("id"):
            anchors.append(el["id"])
        anchors.extend(x["id"] for x in el.find_all(id=True))
    if u.kind == "prose" and u.section_anchor:
        anchors.insert(0, u.section_anchor)
    u.text = "\n\n".join(texts)
    u.refs = list(dict.fromkeys(refs))
    u.anchors = [a for a in dict.fromkeys(anchors) if not a.startswith("VUID-")]
    u.elements = []
    return u


def parse_sections(entities: set[str]) -> tuple[list[Unit], dict, dict[str, str]]:
    """Return (units, stats, heading_fallback)."""
    html = (BUILD / "vkspec.html").read_text(encoding="utf-8")
    sp = SectionParser(html, entities)
    units = [finalize(u) for u in sp.parse()]
    return units, sp.stats, sp.heading_fallback
