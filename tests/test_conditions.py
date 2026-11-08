import pytest

from vkrag.conditions import CORE, conj, conj_all, from_str, parse_ifdef, to_str, version_of


def test_or():
    assert parse_ifdef("VK_VERSION_1_3,VK_KHR_dynamic_rendering") == frozenset(
        {frozenset({"VK_VERSION_1_3"}), frozenset({"VK_KHR_dynamic_rendering"})}
    )


def test_and():
    assert parse_ifdef("VK_NV_ray_tracing+VK_KHR_acceleration_structure") == frozenset(
        {frozenset({"VK_NV_ray_tracing", "VK_KHR_acceleration_structure"})}
    )


def test_nested_is_and_and_distributes():
    d = conj_all([parse_ifdef("A,B"), parse_ifdef("C")])
    assert to_str(d) == "A+C,B+C"


def test_absorption():
    d = conj(parse_ifdef("A,B"), parse_ifdef("A"))
    assert to_str(d) == "A"


def test_core_identity():
    assert conj(CORE, parse_ifdef("X")) == parse_ifdef("X")
    assert to_str(CORE) == "core"


def test_roundtrip():
    s = "A+C,B+C"
    assert to_str(from_str(s)) == s


def test_mixed_plus_binds_tighter():
    assert to_str(parse_ifdef("VK_COMPUTE_VERSION_1_4,VK_EXT_a+VK_EXT_b")) == "VK_COMPUTE_VERSION_1_4,VK_EXT_a+VK_EXT_b"


@pytest.mark.parametrize(
    "src,expected",
    [
        ("VK_GRAPHICS_VERSION_1_0", "VK_VERSION_1_0"),
        ("VK_COMPUTE_VERSION_1_0+VK_EXT_mesh_shader", "VK_EXT_mesh_shader"),
        ("VK_GRAPHICS_VERSION_1_0+VK_GRAPHICS_VERSION_1_2", "VK_VERSION_1_2"),
        ("VK_BASE_VERSION_1_3,VK_KHR_synchronization2", "VK_KHR_synchronization2,VK_VERSION_1_3"),
        ("core", "core"),
    ],
)
def test_simplify_versions(src, expected):
    from vkrag.conditions import simplify_versions

    assert to_str(simplify_versions(from_str(src))) == expected


@pytest.mark.parametrize("bad", ["", "A,", "A,+C", "+A"])
def test_bad(bad):
    with pytest.raises(ValueError):
        parse_ifdef(bad)


@pytest.mark.parametrize(
    "name,ver",
    [("VK_VERSION_1_3", (1, 3)), ("VK_BASE_VERSION_1_1", (1, 1)), ("VK_GRAPHICS_VERSION_1_4", (1, 4)),
     ("VK_COMPUTE_VERSION_1_2", (1, 2)), ("VK_KHR_maintenance1", None)],
)
def test_version_of(name, ver):
    assert version_of(name) == ver
