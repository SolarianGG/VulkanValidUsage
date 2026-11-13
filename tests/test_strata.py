"""Stage 2: stratum assignment (PLAN §9.3 examples), sampling, gpuinfo parsing, history helpers."""

from datetime import date

import pytest

from vkrag.conditions import from_str
from vkrag.history import select_tags, text_change
from vkrag.ingest.gpuinfo import combine, parse_page
from vkrag.strata import Registry, base_stratum, exclusion, sample

REG = {
    "entities": {
        "vkCmdDraw": {"canonical": "vkCmdDraw", "core_version": "1.0", "extensions": []},
        "vkCmdBeginRendering": {"canonical": "vkCmdBeginRendering", "core_version": "1.3", "extensions": []},
        "vkCmdDrawMeshTasksEXT": {"canonical": "vkCmdDrawMeshTasksEXT", "core_version": None, "extensions": ["VK_EXT_mesh_shader"]},
        "vkCmdBeginRenderingKHR": {"canonical": "vkCmdBeginRendering", "core_version": "1.3", "extensions": []},
        "vkCreateExecutionGraphPipelinesAMDX": {"canonical": "x", "core_version": None, "extensions": ["VK_AMDX_shader_enqueue"]},
        "vkCmdDebugMarkerBeginEXT": {"canonical": "x", "core_version": None, "extensions": ["VK_EXT_debug_marker"]},
    },
    "extensions": {
        "VK_KHR_dynamic_rendering": {"promotedto": "VK_VERSION_1_3"},
        "VK_EXT_shader_object": {"promotedto": None},
        "VK_EXT_mesh_shader": {"promotedto": None},
        "VK_NV_mesh_shader": {"promotedto": None},
        "VK_EXT_line_rasterization": {"promotedto": "VK_KHR_line_rasterization"},
        "VK_KHR_line_rasterization": {"promotedto": "VK_VERSION_1_4"},
        "VK_AMDX_shader_enqueue": {"promotedto": None, "provisional": True},
        "VK_EXT_debug_marker": {"promotedto": None, "specialuse": "debugging"},
        "VK_KHR_maintenance5": {"promotedto": "VK_VERSION_1_4", "deprecatedby": None},
    },
}
COV = {"VK_EXT_shader_object": 0.70, "VK_EXT_mesh_shader": 0.49, "VK_NV_mesh_shader": 0.9}


@pytest.fixture
def reg():
    return Registry(REG, {"vkCmdBeginRenderingKHR": "vkCmdBeginRendering"}, COV)


def st(reg, entity, cond, thr=0.5):
    return base_stratum(reg, from_str(cond), entity, thr)


def test_plan_examples(reg):
    assert st(reg, "vkCmdDraw", "core")["base"] == "core_1_0"
    r = st(reg, "vkCmdDraw", "VK_KHR_dynamic_rendering,VK_VERSION_1_3")
    assert r["base"] == "core_promoted" and r["core_version"] == "1.3"
    assert st(reg, "vkCmdDraw", "VK_EXT_shader_object")["base"] == "ext_popular"
    assert st(reg, "vkCmdDraw", "VK_EXT_shader_object", thr=0.8)["base"] == "ext_niche"
    r = st(reg, "vkCmdDrawMeshTasksEXT", "core")
    assert r["base"] == "ext_niche" and r["path_extensions"] == ["VK_EXT_mesh_shader"]
    assert st(reg, "vkCmdDrawMeshTasksEXT", "core", thr=0.4)["base"] == "ext_popular"
    # vendor extension counts as coverage 0 even if widely reported
    assert st(reg, "vkCmdDraw", "VK_NV_mesh_shader")["base"] == "ext_niche"


def test_core_version_of_entity_and_promotion_chain(reg):
    assert st(reg, "vkCmdBeginRendering", "core")["base"] == "core_promoted"
    assert st(reg, "vkCmdBeginRenderingKHR", "core")["core_version"] == "1.3"  # alias resolves
    r = st(reg, "vkCmdDraw", "VK_EXT_line_rasterization")  # EXT -> KHR -> 1.4
    assert r["base"] == "core_promoted" and r["core_version"] == "1.4" and r["cond_ext_only_promoted"]
    # promoted + non-promoted in one clause: extension path over the non-promoted one only
    r = st(reg, "vkCmdDraw", "VK_EXT_shader_object+VK_KHR_maintenance5")
    assert r["base"] == "ext_popular" and r["path_extensions"] == ["VK_EXT_shader_object"]
    # an OR with a core clause wins
    assert st(reg, "vkCmdDraw", "VK_EXT_mesh_shader,VK_VERSION_1_1")["base"] == "core_promoted"


def test_unknown_names_and_origin(reg):
    r = st(reg, "vkCmdDraw", "VK_FOO_bar")
    assert r["base"] is None and r["unknown_names"] == ["VK_FOO_bar"]
    r = st(reg, "Position", "core")  # built-in outside vk.xml
    assert r["base"] == "core_1_0" and r["origin_unknown"]


def test_exclusions(reg):
    assert exclusion(reg, from_str("VK_AMDX_shader_enqueue"), "vkCmdDraw")[0] == "provisional_condition"
    assert exclusion(reg, from_str("core"), "vkCreateExecutionGraphPipelinesAMDX")[0] == "provisional_entity"
    assert exclusion(reg, from_str("core"), "vkCmdDebugMarkerBeginEXT")[0] == "specialuse_entity"
    reason, flags = exclusion(reg, from_str("VK_EXT_debug_marker"), "vkCmdDraw")
    assert reason is None and flags == {"cond_specialuse": True}


def _cands():
    out = []
    for s in ("a", "b"):
        for e in range(6):
            for k in range(4):
                out.append({"stratum": s, "entity": f"E{e}", "vuid": f"V-{s}-{e}-{k}", "equiv_class_id": f"c-{s}-{e}-{k % 3}"})
    return out


def test_sampling_constraints_and_determinism():
    c = _cands()
    a = sample(c, {"a": 10, "b": 10}, 3, seed=1)
    assert a == sample(list(reversed(c)), {"a": 10, "b": 10}, 3, seed=1)  # input order does not matter
    per_entity = {}
    for r in a:
        per_entity[r["entity"]] = per_entity.get(r["entity"], 0) + 1
    assert max(per_entity.values()) <= 3  # global cap across strata
    assert len({r["equiv_class_id"] for r in a}) == len(a)
    pilot = sample(c, {"a": 3, "b": 3}, 3, seed=2, used_vuids={r["vuid"] for r in a}, used_classes={r["equiv_class_id"] for r in a})
    assert not {r["vuid"] for r in pilot} & {r["vuid"] for r in a}
    assert not {r["equiv_class_id"] for r in pilot} & {r["equiv_class_id"] for r in a}


PAGE = """<!-- saved from url=(0060)https://vulkan.gpuinfo.org/listextensions.php?platform=linux -->
<select name="age" id="age"><option value="recent" selected="">Recent (1y)</option><option value="historic">Historic</option></select>
<table><thead><tr role="row"><th></th></tr><tr role="row"><th>Extension</th></tr></thead><tbody>
<tr role="row" class="even"><td class="sorting_1"><a href="x">VK_EXT_mesh_shader</a></td><td class="centered"><a class="c" href="y">48.39<span style="font-size:10px;">%</span></a></td><td class="centered"><a class="na" href="z">51.61<span style="font-size:10px;">%</span></a></td><td class="centered">2022-09-01</td><td></td></tr>
<tr role="row" class="odd"><td class="sorting_1"><a href="x">VK_KHR_swapchain</a></td><td class="centered"><a class="c" href="y">100<span style="font-size:10px;">%</span></a></td><td class="centered"><a class="na" href="z">0<span style="font-size:10px;">%</span></a></td><td class="centered">2016-02-16</td><td></td></tr>
</tbody></table>"""


def test_gpuinfo_parse_and_combine():
    p = parse_page(PAGE)
    assert p["coverage"] == {"VK_EXT_mesh_shader": 0.4839, "VK_KHR_swapchain": 1.0}
    assert p["filters"]["age"]["label"] == "Recent (1y)" and p["table_rows"] == 2
    inst = parse_page(
        '<tr role="row" class="odd"><td class="value sorting_1">VK_KHR_surface</td><td class="text-center"><a class="supported" href="x">99.5<span style="font-size:10px;">%</span></a></td><td class="text-center"><a class="na" href="y">0.5<span style="font-size:10px;">%</span></a></td><td class="value">2016-02-16</td></tr>'
    )
    assert inst["coverage"] == {"VK_KHR_surface": 0.995} and inst["table_rows"] == 1
    per = {"windows": {"VK_KHR_win32_surface": 0.99, "VK_EXT_x": 0.6}, "linux": {"VK_EXT_x": 0.2}}
    plat = {"VK_KHR_win32_surface": "win32"}
    assert combine(per, plat, "mean") == {"VK_EXT_x": 0.4, "VK_KHR_win32_surface": 0.495}
    assert combine(per, plat, "platform") == {"VK_EXT_x": 0.4, "VK_KHR_win32_surface": 0.99}


def test_history_window_and_text_change():
    dates = {
        "v1.3.200": "2021-12-01",
        "v1.3.269": "2023-11-03",
        "v1.3.270": "2023-11-10",
        "v1.4.300": "2024-06-01",
        "v1.4.400": "2027-01-01",
    }
    tags, start = select_tags(dates, "v1.4.300", date(2026, 11, 7), 3)
    assert start == "2023-11-07" and tags == ["v1.3.269", "v1.3.270", "v1.4.300"]
    same = text_change("buffer must be  bound", "buffer must be bound", 0.1)
    assert not same["changed"]
    ren = text_change("pname:x must be a vkCmdBeginRenderingKHR call", "pname:x must be a vkCmdBeginRendering call", 0.1)
    assert ren["changed"] and ren["ids_added"] == ["vkCmdBeginRendering"]
