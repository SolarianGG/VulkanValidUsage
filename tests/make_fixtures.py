"""Cut real fragments of the built spec into tests/fixtures/ (run once after `vkrag spec build`)."""

import json
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures"
OUT.mkdir(exist_ok=True)

vu = json.load(open(ROOT / "data/build/validusage.json", encoding="utf-8"))["validation"]
flat = {e["vuid"]: e["text"] for b in vu.values() for l in b.values() for e in l}
want = [
    "VUID-VkRenderingInfo-pNext-06112",  # TeX ceil/frac
    "VUID-vkCmdWaitEvents2-dependencyFlags-10394",  # nested list
    "VUID-VkAccelerationStructureGeometryTrianglesDataKHR-vertexStride-03819",  # eq + sup
    "VUID-vkGetFenceFdKHR-handleType-01454",  # &#8217;
    "VUID-vkCmdDraw-None-08606",  # links to features
]
picked = {k: flat[k] for k in want if k in flat}
# top up by features if some VUIDs were not found
for k, t in flat.items():
    if len(picked) >= 8:
        break
    if ("<sup>" in t or "&#8217;" in t or "\\over" in t) and k not in picked:
        picked[k] = t
(OUT / "vu_texts.json").write_text(json.dumps(picked, indent=1, ensure_ascii=False), encoding="utf-8")

h = open(ROOT / "data/build/vkspec.html", encoding="utf-8").read()
soup = BeautifulSoup(h, "lxml")
cp = soup.find(id="vkCmdDraw").find_parent("div", class_="openblock")
props = next(
    t
    for t in cp.find_all("div", class_="sidebarblock")
    if t.select_one(".title") and t.select_one(".title").get_text() == "Command Properties"
)
(OUT / "command_properties.html").write_text(str(props), encoding="utf-8")
frac = soup.select_one(".mfrac").find_parent(class_="katex")
(OUT / "katex_frac.html").write_text(str(frac), encoding="utf-8")
sup = next(k for k in soup.select(".katex") if k.select_one(".msupsub") and not k.select_one(".mfrac"))
(OUT / "katex_supsub.html").write_text(str(sup), encoding="utf-8")
print("fixtures:", [p.name for p in OUT.iterdir()], "vu:", list(picked))
