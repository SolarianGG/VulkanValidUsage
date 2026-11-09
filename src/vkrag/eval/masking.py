"""Answer masking before the judge (PLAN §7.2, §9.3): configuration markers and VUIDs are removed so the
judge cannot tell RAG from closed-book answers. VUIDs are checked separately by the automatic checks."""
from __future__ import annotations

import re

VUID_TOKEN = "[VUID]"
# (pattern, replacement); case-insensitive, applied in order
PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bVUID-[A-Za-z0-9_-]+\b", re.I), VUID_TOKEN),
    # VUIDs cited without the prefix: vkCmdResetEvent2-stageMask-03929, VkFoo-bar-01234
    (re.compile(r"\b(?:vk|Vk|VK)[A-Za-z0-9_]*-[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*-\d{5}\b"), VUID_TOKEN),
    (re.compile(r"\bthe (?:provided |given )?(?:context|documents?|excerpts?|passages?) (?:does not|doesn't|do not|don't) "
                r"(?:explicitly )?(?:mention|contain|say|cover|address|state|include)[^.]*\.", re.I), ""),
    (re.compile(r"\b(?:according to|based on|per|as stated in|as shown in|from|in) the (?:provided |given )?"
                r"(?:context|documents?|excerpts?|passages?)\b[^.,;:]*", re.I), ""),
    (re.compile(r"\b(?:context|passage|excerpt|chunk|item) \[?\d+\]?", re.I), ""),
    (re.compile(r"\[\d+\]"), ""),
    (re.compile(r"\bfrom (?:my|general) (?:own )?knowledge\b[^.]*", re.I), ""),
    (re.compile(r"\b(?:I am |I'm |I )?(?:relying|rely|relies|drawing|based) (?:on|from) (?:my )?(?:own |general )?knowledge\b[^.)]*", re.I), ""),
    (re.compile(r",? ?as permitted by the instructions\b", re.I), ""),
    (re.compile(r"\(?\b(?:from )?general (?:spec(?:ification)? |Vulkan )?knowledge(?:, not in (?:the )?context)?\)?", re.I), ""),
    (re.compile(r",? ?\bnot (?:in|from) (?:the )?context\b", re.I), ""),
    (re.compile(r"\(?\b(?:cited |listed )?(?:from|in|based on) (?:the )?context\b\)?", re.I), ""),
    (re.compile(r"/Context\b"), ""),  # "Relevant VUIDs/Context:"
    (re.compile(r"\bContext (Analysis|Limitation|Match)\b"), r"\1"),
    (re.compile(r"\((?:VU|Section: [^)\n]*)\)"), ""),  # context item labels copied into the answer
    (re.compile(r"\b(VUIDs?|(?:validation )?rules?|(?:source )?text|(?:\w+ )?description|sections?)(?: you)? provided\b", re.I), r"\1"),
    (re.compile(r"\b(?:your|my) context(?: text)?\b", re.I), "the specification"),
    (re.compile(r"\*{0,2}\b(?:the )?snippets?\b\s*\*{0,2}", re.I), "the specification "),
    (re.compile(r"\b(the (?:\w+ ){0,2}(?:specification|text|documentation|sections?)) provided\b", re.I), r"\1"),
    # remaining mentions of the context are replaced by a neutral phrase (deleting them breaks sentences)
    (re.compile(r"\b(?:the |this )?(?:provided |given |above |supplied )(?:context|text|snippets?|excerpts?|passages?|documents?|"
                r"documentation|information)(?: (?:snippets?|passages?|excerpts?))?\b", re.I), "the specification"),
    (re.compile(r"\b(?:the |this )context(?: (?:snippets?|passages?|excerpts?|items?))?\b", re.I), "the specification"),
    (re.compile(r"\bthe provided\b(?!\s+[a-z])", re.I), "the specification"),  # dangling after removed [n]
    (re.compile(r"\*\*\s*\*\*"), ""),  # bold markers left around a removed [n] / VUID
]


def mask(text: str) -> tuple[str, bool]:
    """Masked text and whether anything other than a VUID was removed (config marker hit)."""
    out, marker = text, False
    for _ in range(3):  # to a fixed point: a later pattern can expose an earlier one
        before = out
        for i, (pat, rep) in enumerate(PATTERNS):
            new = pat.sub(rep, out)
            if i >= 2 and new != out:
                marker = True
            out = new
        if out == before:
            break
    out = re.sub(r"\(\s*(?:\[VUID\]\s*,?\s*)*\)", lambda m: "" if "[VUID]" not in m.group(0) else m.group(0), out)
    out = re.sub(r"\(\s*\)", "", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r" +([.,;:])", r"\1", out)
    out = re.sub(r"(^|\n)\s*[,;:]\s*", r"\1", out)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    if out[:1].islower():  # "Based on the context, here is ..." -> "Here is ..."
        out = out[0].upper() + out[1:]
    return out, marker
