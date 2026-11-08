"""HTML (built spec / validusage.json fragments) -> plain text.

- links: the text is kept, the target anchor `href="#..."` goes to refs;
- `<strong>`, `<code>`, `<em>`: text only;
- lists -> `- item` lines (indented when nested);
- tables -> `Header: value; ...` lines (Command Properties etc.);
- TeX `\\(...\\)` from json -> readable text (ceil(...), (a)/(b), ×);
- KaTeX markup from HTML -> linear text (fractions, sub/superscripts);
- HTML entities are unescaped, whitespace is collapsed.
"""
from __future__ import annotations

import html as htmllib
import re

from bs4 import BeautifulSoup, NavigableString, Tag

# ---------------------------------------------------------------- TeX → text

_TEX_SIMPLE = {
    r"\times": "×", r"\cdot": "·", r"\leq": "≤", r"\le": "≤", r"\geq": "≥", r"\ge": "≥",
    r"\neq": "≠", r"\ne": "≠", r"\lt": "<", r"\gt": ">", r"\pm": "±", r"\infty": "∞",
    r"\lvert": "|", r"\rvert": "|", r"\vert": "|", r"\mid": "|", r"\ldots": "...", r"\cdots": "...",
    r"\log": "log", r"\min": "min", r"\max": "max", r"\sum": "sum", r"\in": "∈",
    r"\_": "_", r"\,": " ", r"\;": " ", r"\!": "", r"\quad": " ", r"\qquad": " ",
}
_TEX_WRAP = ("mathit", "mathtt", "textrm", "text", "mathrm", "mathbf", "textit", "texttt", "mathsf", "operatorname", "mathbin")


def _read_group(s: str, i: int) -> tuple[str, int]:
    """Read a {group} or a single token starting at position i (after spaces)."""
    while i < len(s) and s[i] == " ":
        i += 1
    if i < len(s) and s[i] == "{":
        depth, j = 0, i
        while j < len(s):
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                depth -= 1
                if depth == 0:
                    return s[i + 1 : j], j + 1
            j += 1
        return s[i + 1 :], len(s)
    if i < len(s) and s[i] == "\\":
        m = re.match(r"\\[A-Za-z]+|\\.", s[i:])
        return m.group(0), i + len(m.group(0))
    return (s[i], i + 1) if i < len(s) else ("", i)


def _paren(x: str) -> str:
    x = x.strip()
    return x if re.fullmatch(r"[\w.]+", x) else f"({x})"


def tex_to_text(s: str) -> str:
    s = s.strip()
    # {a \over b} → \frac{a}{b}
    while r"\over" in s:
        m = re.search(r"\\over\b", s)
        # enclosing group: walk left to the unmatched '{' and right to the unmatched '}'
        lo, depth = -1, 0
        for j in range(m.start() - 1, -1, -1):
            if s[j] == "}":
                depth += 1
            elif s[j] == "{":
                if depth == 0:
                    lo = j
                    break
                depth -= 1
        hi, depth = None, 0
        for j in range(m.end(), len(s)):
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                if depth == 0:
                    hi = j
                    break
                depth -= 1
        if lo == -1 or hi is None:
            num, den = s[: m.start()], s[m.end() :]
            s = rf"\frac{{{num}}}{{{den}}}"
        else:
            num, den = s[lo + 1 : m.start()], s[m.end() : hi]
            s = s[:lo] + rf"{{\frac{{{num}}}{{{den}}}}}" + s[hi + 1 :]
    out: list[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+|.)", s[i:])
            cmd = m.group(1)
            i += len(m.group(0))
            if cmd == "frac":
                a, i = _read_group(s, i)
                b, i = _read_group(s, i)
                out.append(f"{_paren(tex_to_text(a))}/{_paren(tex_to_text(b))}")
            elif cmd == "sqrt":
                a, i = _read_group(s, i)
                out.append(f"sqrt({tex_to_text(a)})")
            elif cmd in ("left", "right"):
                continue
            elif cmd in ("lceil", "lfloor"):
                out.append("ceil(" if cmd == "lceil" else "floor(")
            elif cmd in ("rceil", "rfloor"):
                out.append(")")
            elif cmd in _TEX_WRAP:
                a, i = _read_group(s, i)
                out.append(tex_to_text(a))
            elif "\\" + cmd in _TEX_SIMPLE:
                out.append(_TEX_SIMPLE["\\" + cmd])
            else:
                out.append(cmd)
        elif c in "_^":
            a, i = _read_group(s, i + 1)
            t = tex_to_text(a)
            out.append(c + (t if re.fullmatch(r"\w+", t) else f"{{{t}}}"))
        elif c in "{}":
            i += 1
        else:
            out.append(c)
            i += 1
    text = "".join(out)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\(\s+", "(", text)
    return re.sub(r"\s+\)", ")", text).strip()


# ---------------------------------------------------------------- KaTeX HTML → text


def _top(el: Tag) -> float:
    m = re.search(r"top:\s*(-?[\d.]+)em", el.get("style", ""))
    return float(m.group(1)) if m else 0.0


def _katex_text(el) -> str:
    if isinstance(el, NavigableString):
        return str(el).replace("\u200b", "").replace("\u2212", "-")
    cls = el.get("class", [])
    if el.name == "svg" or any(c in cls for c in ("strut", "pstrut", "frac-line", "vlist-s", "katex-mathml")):
        return ""
    if "mfrac" in cls:
        parts = [sp for sp in el.select_one(".vlist").find_all("span", recursive=False) if not sp.select_one(".frac-line")]
        parts.sort(key=_top)  # the most negative top is the numerator
        txt = [_katex_text(p).strip() for p in parts]
        txt = [t for t in txt if t]
        if len(txt) == 2:
            return f"{_paren(txt[0])}/{_paren(txt[1])}"
        return " ".join(txt)
    if "msupsub" in cls:
        vl = el.select_one(".vlist")
        res = []
        for sp in sorted(vl.find_all("span", recursive=False), key=_top) if vl else []:
            t = _katex_text(sp).strip()
            if not t:
                continue
            mark = "^" if _top(sp) < -2.75 else "_"
            res.append(mark + (t if re.fullmatch(r"\w+", t) else f"{{{t}}}"))
        # output order: subscript first, then superscript
        return "".join(sorted(res, key=lambda x: x[0] != "_"))
    if "sqrt" in cls:
        vl = el.select_one(".vlist")
        inner = [_katex_text(sp).strip() for sp in vl.find_all("span", recursive=False)] if vl else []
        return "sqrt(" + " ".join(t for t in inner if t) + ")"
    return "".join(_katex_text(c) for c in el.children)


def katex_to_text(el: Tag) -> str:
    root = el.select_one(".katex-html") or el
    t = _katex_text(root)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------- HTML → text

_BLOCK = {"p", "div", "ul", "ol", "li", "table", "tr", "pre", "br", "dl", "dt", "dd", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"}
TEX_INLINE = re.compile(r"\\\((.*?)\\\)", re.S)


class _Walker:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.refs: list[str] = []

    def nl(self) -> None:
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def walk(self, el, depth: int = 0) -> None:
        if isinstance(el, NavigableString):
            if el.__class__.__name__ in ("Comment", "Doctype"):
                return
            self.parts.append(re.sub(r"\s+", " ", str(el)))  # a newline in HTML is whitespace
            return
        if not isinstance(el, Tag):
            return
        cls = el.get("class", [])
        if el.name in ("script", "style"):
            return
        if "katex" in cls or "katex-display" in cls:
            k = el if "katex" in cls else el.select_one(".katex")
            if "katex-display" in cls:
                self.nl()
            self.parts.append(katex_to_text(k) if k else "")
            if "katex-display" in cls:
                self.nl()
            return
        if el.name == "a":
            href = el.get("href", "")
            if href.startswith("#") and not href.startswith("#VUID-"):
                self.refs.append(href[1:])
            if not el.get_text() and el.get("id", "").startswith("VUID-"):
                return
        if el.name == "span" and "vuid" in cls:
            return  # the VUID label in HTML; it is kept in metadata
        if el.name == "br":
            self.nl()
            return
        if el.name == "sub":
            self.parts.append("_" + el.get_text())
            return
        if el.name == "sup":
            self.parts.append("^" + el.get_text())
            return
        if el.name == "table":
            self._table(el)
            return
        if el.name == "li":
            self.nl()
            self.parts.append("  " * depth + "- ")
            for c in el.children:
                self.walk(c, depth)
            self.nl()
            return
        if el.name in ("ul", "ol", "dl"):
            self.nl()
            for c in el.children:
                self.walk(c, depth + 1 if el.find_parent("li") else depth)
            self.nl()
            return
        if el.name == "div" and "title" in cls:
            self.nl()
            self.parts.append(el.get_text().strip() + ":")
            self.nl()
            return
        if el.name == "pre":
            self.nl()
            self.parts.append(el.get_text())
            self.nl()
            return
        block = el.name in _BLOCK
        if block and el.name == "p" and el.parent is not None and el.parent.name == "li" and el is el.parent.find(True):
            block = False  # first paragraph of a list item stays on the bullet line
        if block:
            self.nl()
        for c in el.children:
            self.walk(c, depth)
        if block:
            self.nl()

    def _table(self, t: Tag) -> None:
        rows = t.find_all("tr")
        head = [c.get_text(" ", strip=True) for c in rows[0].find_all(["th"])] if rows else []
        self.nl()
        for tr in rows:
            for a in tr.select("a[href^='#']"):
                self.refs.append(a["href"][1:])
            cells = [re.sub(r"\s+", " ", c.get_text(" / ", strip=True)) for c in tr.find_all(["td", "th"])]
            if not cells or (head and cells == head):
                continue
            if head and len(head) == len(cells):
                self.parts.append("; ".join(f"{h}: {v}" for h, v in zip(head, cells)))
            else:
                self.parts.append(" | ".join(cells))
            self.nl()


def _clean(text: str) -> str:
    text = htmllib.unescape(text)
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    lines = []
    for ln in text.split("\n"):
        ln = re.sub(r"[ \t]+", " ", ln).rstrip()
        indent = re.match(r"^ *", ln).group(0) if ln.lstrip().startswith("- ") else ""
        lines.append(indent + ln.strip())
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def html_to_text(node: str | Tag) -> tuple[str, list[str]]:
    """Return (text, refs); refs are deduplicated, in order of appearance."""
    if isinstance(node, str):
        node = TEX_INLINE.sub(lambda m: tex_to_text(m.group(1)), node)
        node = BeautifulSoup(node, "lxml")
    w = _Walker()
    w.walk(node)
    text = "".join(w.parts)
    text = TEX_INLINE.sub(lambda m: tex_to_text(m.group(1)), text)
    # stray spaces before punctuation left after markup removal
    text = re.sub(r" +([,.;:)])", r"\1", text)
    return _clean(text), list(dict.fromkeys(w.refs))
