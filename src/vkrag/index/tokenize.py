"""BM25 tokenizer (PLAN §4 Stage 4), also used by the question n-gram leak filter (Stage 3).

- An identifier (token with `_`, an inner capital, or a `vk`/`Vk`/`VK_` prefix) is kept whole,
  lowercased and never stemmed, and additionally split into its camelCase / SNAKE_CASE parts.
  The `vk` prefix part is dropped (`vkCmdBindPipeline` -> `vkcmdbindpipeline cmd bind pipeline`).
- Identifier parts and plain words are lowercased, English stop words are removed, and they are
  stemmed (Snowball English) when `stem=True`; parts are words, so they must match prose forms.
- Version-like numbers (`1.3`) are kept as one token.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

TOKEN = re.compile(r"\d+(?:\.\d+)+|[A-Za-z_][A-Za-z0-9_]*|\d+")
CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")

# English stop words (the bm25s / sklearn-style core list, without words meaningful in VU rules
# such as "not", "no", "must", "only", "all", "any", "each").
STOPWORDS = frozenset("""
a about above after again against am an and are as at be because been before being below between
both but by can could did do does doing down during few for from further had has have having he her
here hers herself him himself his how i if in into is it its itself just me more most my myself nor
of off on once or other our ours ourselves out over own same she should so some such than that the
their theirs them themselves then there these they this those through to too under until up very
was we were what when where which while who whom why will with would you your yours yourself
yourselves
""".split())


def is_identifier(tok: str) -> bool:
    if "_" in tok.strip("_"):
        return True
    if tok[:2] in ("vk", "Vk") and len(tok) > 2 and tok[2].isupper():
        return True
    return any(c.isupper() for c in tok[1:]) and any(c.islower() for c in tok)


def split_identifier(tok: str) -> list[str]:
    parts: list[str] = []
    for piece in tok.split("_"):
        parts += CAMEL.findall(piece)
    parts = [p.lower() for p in parts if p]
    if parts and parts[0] == "vk":
        parts = parts[1:]
    return parts


@lru_cache(maxsize=1)
def _stemmer():
    import Stemmer

    return Stemmer.Stemmer("english")


@dataclass(frozen=True)
class Token:
    text: str
    identifier: bool  # the whole identifier, not one of its parts
    part: bool = False  # a part of a split identifier


def tokens(text: str, stem: bool = True, stopwords: bool = True) -> list[Token]:
    out: list[Token] = []
    st = _stemmer() if stem else None

    def word(w: str, part: bool) -> None:
        w = w.lower()
        if stopwords and w in STOPWORDS:
            return
        if st and not w[0].isdigit():
            w = st.stemWord(w)
        out.append(Token(w, False, part))

    for m in TOKEN.finditer(text):
        t = m.group(0)
        if t[0].isdigit():
            out.append(Token(t, False))
        elif is_identifier(t):
            out.append(Token(t.lower(), True))
            for p in split_identifier(t):
                word(p, True)
        else:
            word(t, False)
    return out


def tokenize(text: str, stem: bool = True) -> list[str]:
    """Token strings for BM25 indexing and querying."""
    return [t.text for t in tokens(text, stem=stem)]


def content_words(text: str) -> list[str]:
    """Unstemmed non-identifier words without stop words (n-gram leak filter, PLAN §4 Stage 3)."""
    return [t.text for t in tokens(text, stem=False) if not t.identifier and not t.part]


def plain_words(text: str) -> list[str]:
    """Unstemmed non-identifier words with stop words kept (the stricter leak variant, PLAN §10)."""
    return [t.text for t in tokens(text, stem=False, stopwords=False) if not t.identifier and not t.part]


def leak_ngrams(question: str, vu_text: str) -> tuple[int, int]:
    """(content-word n-gram, n-gram with stop words) shared by a question and its VU text."""
    return (max_common_ngram(content_words(question), content_words(vu_text)),
            max_common_ngram(plain_words(question), plain_words(vu_text)))


def max_common_ngram(a: list[str], b: list[str]) -> int:
    """Length of the longest common contiguous run of tokens (longest common substring)."""
    if not a or not b:
        return 0
    best = 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            if x == y:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best
