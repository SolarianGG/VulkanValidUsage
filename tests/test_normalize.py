"""Normalization on real fragments of the built spec v1.4.366 (tests/fixtures, see make_fixtures.py)."""

import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from vkrag.normalize import html_to_text, katex_to_text, tex_to_text

FX = Path(__file__).parent / "fixtures"
VU = json.loads((FX / "vu_texts.json").read_text(encoding="utf-8"))


def test_tex_ceil_frac():
    t, refs = html_to_text(VU["VUID-VkRenderingInfo-pNext-06112"])
    assert "ceil((renderArea_x+renderArea_width)/maxFragmentDensityTexelSize_width)" in t
    assert "\\" not in t
    assert refs == ["VkDeviceGroupRenderPassBeginInfo", "VkRenderingFragmentDensityMapAttachmentInfoEXT", "VK_NULL_HANDLE"]


def test_nested_list():
    t, refs = html_to_text(VU["VUID-vkCmdWaitEvents2-dependencyFlags-10394"])
    lines = t.split("\n")
    assert lines[0].endswith("the following bits:")
    assert "- VK_DEPENDENCY_BY_REGION_BIT" in lines
    assert "- VK_DEPENDENCY_VIEW_LOCAL_BIT" in lines
    assert refs == ["VkDependencyFlagBits"]


def test_eq_sup():
    t, _ = html_to_text(VU["VUID-VkAccelerationStructureGeometryTrianglesDataKHR-vertexStride-03819"])
    assert t == "vertexStride must be less than or equal to 2^32-1"


def test_entities_and_member_ref():
    t, refs = html_to_text(VU["VUID-VkFenceGetWin32HandleInfoKHR-handleType-01448"])
    assert "VkExportFenceCreateInfo::handleTypes" in t
    assert "fence’s current payload" in t
    assert "<" not in t and "&#" not in t


def test_feature_ref_kept_as_anchor():
    t, refs = html_to_text(VU["VUID-vkCmdDraw-None-08606"])
    assert t.startswith("If the shaderObject feature is not enabled")
    assert refs == ["features-shaderObject"]


def test_command_properties_table():
    t, refs = html_to_text((FX / "command_properties.html").read_text(encoding="utf-8"))
    assert "Command Buffer Levels: Primary / Secondary" in t
    assert "Render Pass Scope: Inside" in t
    assert "Supported Queue Types: VK_QUEUE_GRAPHICS_BIT" in t
    assert "VkQueueFlagBits" in refs


def test_katex_frac():
    k = BeautifulSoup((FX / "katex_frac.html").read_text(encoding="utf-8"), "lxml").select_one(".katex")
    assert katex_to_text(k) == "f=c/(2^b-1)"


def test_katex_supsub():
    k = BeautifulSoup((FX / "katex_supsub.html").read_text(encoding="utf-8"), "lxml").select_one(".katex")
    t = katex_to_text(k)
    assert t and "​" not in t and ("_" in t or "^" in t)


@pytest.mark.parametrize(
    "tex,expected",
    [
        (r"\textrm{codeSize} \over 4", "codeSize/4"),
        (r"2 \times \mathtt{VK\_UUID\_SIZE}", "2 × VK_UUID_SIZE"),
        (r"\lceil{\mathit{samples} \over 32}\rceil", "ceil(samples/32)"),
    ],
)
def test_tex_real_cases(tex, expected):
    assert tex_to_text(tex) == expected
