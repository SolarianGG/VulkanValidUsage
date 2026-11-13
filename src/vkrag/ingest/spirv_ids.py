"""SPIR-V / GLSL identifier dictionary for the identifier checks (PLAN §3, §4 Stage 3, §7.2).

Sources (pinned, see data/external/spirv_identifiers.meta.json):
  data/raw/SPIRV-Headers  include/spirv/unified1/*.grammar.json: opcode names, enumerants of every
                          operand kind (BuiltIn, Decoration, Capability, StorageClass, ...), operand
                          kind names, extended instruction names (GLSL.std.450 and others)
  data/raw/GLSL           `gl_*` built-in names and `GL_*` extension names from the GLSL spec sources

Output: data/external/spirv_identifiers.txt, one identifier per line, sorted.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from vkrag.config import EXTERNAL, RAW

SPIRV = RAW / "SPIRV-Headers"
GLSL = RAW / "GLSL"
GRAMMAR_DIR = SPIRV / "include" / "spirv" / "unified1"
OUT = EXTERNAL / "spirv_identifiers.txt"
META = EXTERNAL / "spirv_identifiers.meta.json"

GL_BUILTIN = re.compile(r"\bgl_[A-Za-z][A-Za-z0-9_]*")
GL_EXTENSION = re.compile(r"\bGL(?:SL)?_(?:ARB|EXT|KHR|NV|NVX|AMD|ARM|QCOM|HUAWEI|INTEL|OVR|MESA|GOOGLE|OES)_[A-Za-z0-9_]+")
VALID_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _commit(repo: Path) -> dict:
    r = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%H %cI"], capture_output=True, text=True, check=True)
    h, d = r.stdout.split()
    return {"commit": h, "date": d}


def grammar_identifiers(grammar: dict) -> set[str]:
    out: set[str] = set()
    for ins in grammar.get("instructions", []):
        out.add(ins["opname"])
    for kind in grammar.get("operand_kinds", []):
        out.add(kind["kind"])
        for e in kind.get("enumerants", []):
            out.add(e["enumerant"])
            out.update(e.get("aliases", []))
            out.update(e.get("extensions", []))
    for ins in grammar.get("instructions", []):
        out.update(ins.get("aliases", []))
        out.update(ins.get("extensions", []))
    return {x for x in out if VALID_NAME.match(x) and not x.isdigit()}


def glsl_identifiers(root: Path) -> set[str]:
    out: set[str] = set()
    for p in root.rglob("*"):
        if p.suffix not in (".adoc", ".txt") or not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        out.update(GL_BUILTIN.findall(text))
        out.update(GL_EXTENSION.findall(text))
        if p.stem.startswith(("GL_", "GLSL_")):
            out.add(p.stem)
    return {x.rstrip("_") for x in out}


def build() -> dict:
    spirv: set[str] = set()
    grammars = sorted(GRAMMAR_DIR.glob("*.grammar.json"))
    for g in grammars:
        spirv |= grammar_identifiers(json.loads(g.read_text(encoding="utf-8")))
    glsl = glsl_identifiers(GLSL)
    names = sorted(spirv | glsl)
    OUT.write_text("\n".join(names) + "\n", encoding="utf-8")
    meta = {
        "spirv_headers": _commit(SPIRV),
        "glsl": _commit(GLSL),
        "grammars": [g.name for g in grammars],
        "counts": {"spirv": len(spirv), "glsl": len(glsl), "total": len(names)},
    }
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    return meta


def load() -> set[str]:
    return {line.strip() for line in OUT.read_text(encoding="utf-8").splitlines() if line.strip()}
