import random

import pytest

from vkrag.questions import validate as V
from vkrag.questions.prepare import balanced_split, qid_of, quotas


def test_quotas_sum_and_mix():
    q = quotas(80, {"rule": 0.4, "yes_no": 0.3, "scenario": 0.3}, random.Random(1))
    assert q == {"rule": 32, "yes_no": 24, "scenario": 24}
    q = quotas(9, {"rule": 0.4, "yes_no": 0.3, "scenario": 0.3}, random.Random(1))
    assert sum(q.values()) == 9 and all(v == 3 for v in q.values())


def test_balanced_split_alternates_odd_leftovers():
    groups = {f"s{i}": [f"s{i}-{j}" for j in range(3)] for i in range(5)}
    out = balanced_split(groups, ("yes", "no"), random.Random(7))
    assert len(out) == 15
    total = sum(v == "yes" for v in out.values())
    assert total in (7, 8)
    for vs in groups.values():
        assert sum(out[v] == "yes" for v in vs) in (1, 2)


def test_qid_stable_and_style_tagged():
    a = qid_of("pilot", "VUID-vkCmdDraw-None-07888", "identifier")
    assert a == qid_of("pilot", "VUID-vkCmdDraw-None-07888", "identifier")
    assert a.startswith("qp-") and a.endswith("-id")
    assert qid_of("main", "VUID-vkCmdDraw-None-07888", "descriptive").endswith("-de")


class FakeLex:
    vk = {"vkCmdDraw", "VkImageCreateInfo"}
    spirv = {"FragDepth", "Uniform", "Input", "gl_Position", "OpImageWrite"}

    def exists(self, n):
        return n in self.vk or n in self.spirv


@pytest.mark.parametrize(
    "q,expected",
    [
        ("When I copy one image into another, what layout must the destination be in?", []),
        ("Can the image size exceed the limit when flags are zero?", []),
        ("Is vkCmdDraw allowed here?", ["vkCmdDraw"]),
        ("What must srcImageLayout be?", ["srcImageLayout"]),
        ("Can VK_IMAGE_LAYOUT_GENERAL be used?", ["VK_IMAGE_LAYOUT_GENERAL"]),
        ("Must a variable in the Uniform storage class be a block?", ["Uniform"]),
        ("Input variables of a fragment shader: may they be arrays?", []),  # sentence-initial plain word
        ("Can the shader write gl_Position twice?", ["gl_Position"]),
        ("Is a 64 KiB buffer of 65536 bytes enough?", []),
    ],
)
def test_identifiers_in(q, expected):
    assert V.identifiers_in(q, FakeLex()) == expected


ITEM = {
    "vuid": "VUID-X-a-1",
    "entity": "X",
    "entity_kind": "api",
    "stratum": "core_1_0",
    "answer_type": "yes_no",
    "expected_verdict": "no",
    "related_entities": ["Y"],
    "vu_text": "If the image was created with a depth format then the layout must be a depth layout",
}
CTX = {"X": {"VUID-X-a-1", "VUID-X-a-2"}, "Y": {"VUID-Y-b-1"}}


def rec(**kw):
    base = {
        "qid": "q",
        "vuid": "VUID-X-a-1",
        "style": "identifier",
        "answer_type": "yes_no",
        "expected_verdict": "no",
        "question": "Is any layout fine for a depth image?",
        "reference_answer": "No. It must be a depth layout.",
        "checked_entities": ["X"],
        "checked_vuids": [],
        "also_relevant_vuids": [],
    }
    base.update(kw)
    return base


def test_check_answerable_ok():
    assert V.check_answerable(rec(), ITEM, CTX, FakeLex(), 5) == []


def test_vu_number_only_when_it_is_a_suffix_of_the_entity():
    ok = V.check_answerable(rec(question="Is any layout fine for a depth image of 65536 texels?"), ITEM, CTX, FakeLex(), 5)
    assert not any("VU number" in r for r in ok)
    ctx = {**CTX, "X": CTX["X"] | {"VUID-X-a-04121"}}
    bad = V.check_answerable(rec(question="Is rule 04121 about depth images?", checked_vuids=["VUID-X-a-04121"]), ITEM, ctx, FakeLex(), 5)
    assert any("VU number" in r for r in bad)


def test_check_answerable_ngram_leak():
    q = "Is it true that if the image was created with a depth format then the layout must be a depth layout?"
    rs = V.check_answerable(rec(question=q), ITEM, CTX, FakeLex(), 5)
    assert any("n-gram" in r for r in rs)


def test_check_answerable_coverage_and_verdict():
    rs = V.check_answerable(
        rec(checked_entities=[], checked_vuids=["VUID-X-a-1"], expected_verdict="yes", reference_answer="Yes."), ITEM, CTX, FakeLex(), 5
    )
    assert any("miss 1 VUs" in r for r in rs)
    assert any("without verdict_changed" in r for r in rs)


def test_check_scenario_needs_related():
    item = {**ITEM, "answer_type": "scenario"}
    rs = V.check_answerable(
        rec(answer_type="scenario", expected_verdict=None, reference_answer="The layout is wrong."), item, CTX, FakeLex(), 5
    )
    assert any("related entities not checked" in r for r in rs)


def test_descriptive_infeasible_allows_null():
    r = rec(style="descriptive", question=None, reference_answer=None, descriptive_infeasible=True)
    assert V.check_answerable(r, ITEM, CTX, FakeLex(), 5) == []


def test_unanswerable_invented_exists():
    r = {
        "subtype": "nonexistent",
        "question": "How do I call vkCmdDraw?",
        "reference_answer": "x",
        "rationale": "y",
        "invented_identifiers": ["vkCmdDraw"],
    }
    assert any("exists" in x for x in V.check_unanswerable(r, FakeLex()))
