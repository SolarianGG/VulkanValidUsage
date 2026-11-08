import pytest

from vkrag.chunking import availability_label, vu_texts
from vkrag.equivalence import assign_classes
from vkrag.ingest.sections import _clean_title
from vkrag.ingest.vu import split_vuid


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Chapter 21. Drawing Commands", "Drawing Commands"),
        ("21.3. Programmable Primitive Shading", "Programmable Primitive Shading"),
        ("Appendix E: Layers & Extensions (Informative)", "Layers & Extensions (Informative)"),
        ("E.2. List of Current Extensions", "List of Current Extensions"),
        ("Vulkan 1.3 features", "Vulkan 1.3 features"),
        ("Issues", "Issues"),
    ],
)
def test_clean_title(raw, expected):
    assert _clean_title(raw) == expected


@pytest.mark.parametrize(
    "vuid,expected",
    [
        ("VUID-vkCmdDraw-None-08606", ("vkCmdDraw", "None", "08606")),
        ("VUID-VkBufferCreateInfo-sType-sType", ("VkBufferCreateInfo", "sType", "sType")),
        ("VUID-VkBindBufferMemoryInfo-commonparent", ("VkBindBufferMemoryInfo", "", "commonparent")),
        ("VUID-VkBlitImageInfo2KHR-pRegions-06207", ("VkBlitImageInfo2KHR", "pRegions", "06207")),
    ],
)
def test_split_vuid(vuid, expected):
    assert split_vuid(vuid) == expected


def _rec(vuid, entity, text, explicit=True, kind="api", **kw):
    _, param, suffix = split_vuid(vuid)
    r = {"vuid": vuid, "entity": entity, "vuid_entity": entity, "parameter": param, "explicit": explicit,
         "suffix_num": int(suffix) if explicit else None, "text": text, "entity_kind": kind,
         "condition": None, "entity_core_version": None, "entity_extensions": []}
    r.update(kw)
    return r


def test_availability_label_compact():
    r = _rec("VUID-vkCmdX-None-1", "vkCmdX", "t",
             condition="VK_AMD_a+VK_KHR_b+VK_VERSION_1_2,VK_KHR_b+VK_KHR_c,VK_EXT_d+VK_KHR_b")
    assert availability_label(r) == "VK_AMD_a, VK_EXT_d, VK_KHR_b (+2 more)"
    assert availability_label(_rec("VUID-vkCmdX-None-1", "vkCmdX", "t", condition="core", entity_core_version="1.3")) == "Vulkan 1.3"
    assert availability_label(_rec("VUID-vkCmdX-None-1", "vkCmdX", "t", condition="VK_KHR_x,VK_VERSION_1_3")) == "VK_KHR_x, Vulkan 1.3"


def test_vu_texts_header_and_vuid():
    r = _rec("VUID-vkCmdDraw-None-08606", "vkCmdDraw", "rule text", condition="VK_VERSION_1_0", entity_core_version="1.0")
    index_text, llm_text = vu_texts(r)
    assert index_text == "[vkCmdDraw] [Vulkan 1.0]\nrule text"
    assert llm_text.startswith("VUID-vkCmdDraw-None-08606\n")


def test_equivalence_rules():
    recs = [
        _rec("VUID-vkCmdDraw-None-08606", "vkCmdDraw", "same template"),
        _rec("VUID-vkCmdDispatch-None-08606", "vkCmdDispatch", "same template"),       # same suffix
        _rec("VUID-vkCmdFoo-x-00001", "vkCmdFoo", "Identical text"),
        _rec("VUID-vkCmdBar-x-00002", "vkCmdBar", "identical   text"),                 # same raw text
        _rec("VUID-A-A-00003", "A", "The variable decorated with A must be Input", kind="builtin"),
        _rec("VUID-B-B-00004", "B", "The variable decorated with B must be Input", kind="builtin"),
        _rec("VUID-vkCmdFoo-x-parameter", "vkCmdFoo", "Identical text", explicit=False),  # implicit: never merged
    ]
    assign_classes(recs, {}, placeholder=True)
    c = {r["vuid"]: r["equiv_class_id"] for r in recs}
    assert c["VUID-vkCmdDraw-None-08606"] == c["VUID-vkCmdDispatch-None-08606"]
    assert c["VUID-vkCmdFoo-x-00001"] == c["VUID-vkCmdBar-x-00002"]
    assert c["VUID-A-A-00003"] == c["VUID-B-B-00004"]
    assert c["VUID-vkCmdFoo-x-parameter"] not in {c["VUID-vkCmdFoo-x-00001"]}
    assign_classes(recs, {}, placeholder=False)
    c = {r["vuid"]: r["equiv_class_id"] for r in recs}
    assert c["VUID-A-A-00003"] != c["VUID-B-B-00004"]
    assert c["VUID-vkCmdFoo-x-00001"] == c["VUID-vkCmdBar-x-00002"]
