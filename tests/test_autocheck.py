from vkrag.eval.autocheck import VUID_BARE, VUID_FULL, Checker, verdict


class FakeChecker(Checker):
    current = {"vkCmdDraw", "VK_PIPELINE_STAGE_HOST_BIT", "VkBuffer"}
    outdated = {"VK_OLD_NAME_KHR"}
    vu_class = {"VUID-vkCmdDraw-None-02700": "eq-a", "VUID-vkCmdDrawIndexed-None-02700": "eq-a",
                "VUID-vkCmdDraw-None-09999": "eq-b"}


def test_identifiers():
    r = FakeChecker().identifiers("Call vkCmdDraw with VK_OLD_NAME_KHR and vkCmdDrawMagic (VUID-vkCmdFoo-x-12345).")
    assert r["fabricated_identifiers"] == ["vkCmdDrawMagic"] and r["outdated_identifiers"] == ["VK_OLD_NAME_KHR"]


def test_identifier_from_question_not_fabricated():
    r = FakeChecker().identifiers("vkResetPrivateDataSlot does not exist; use vkMagic.", "Does vkResetPrivateDataSlot ...?")
    assert r["fabricated_identifiers"] == ["vkMagic"]


def test_cited_vuids_with_and_without_prefix():
    c = FakeChecker()
    assert c.cited_vuids("VUID-vkCmdDraw-None-02700 and vkCmdDraw-None-09999, again VUID-vkCmdDraw-None-02700") == [
        "VUID-vkCmdDraw-None-02700", "VUID-vkCmdDraw-None-09999"]
    assert VUID_FULL.search("x") is None and VUID_BARE.search("VkBuffer-size-00001")


def test_check_citation_and_verdict():
    q = {"vuid": "VUID-vkCmdDraw-None-02700", "acceptable_vuids": [], "answer_type": "yes_no", "expected_verdict": "no"}
    r = FakeChecker().check("**No.** See VUID-vkCmdDrawIndexed-None-02700 and VUID-vkCmdDraw-None-00000.", q)
    assert r["citation_correct"] and r["citation_precision"] == 0.5
    assert r["fabricated_vuids"] == ["VUID-vkCmdDraw-None-00000"] and r["verdict_match"]


def test_verdict():
    assert verdict("Yes, it is valid") == "yes"
    assert verdict("> No.") == "no"
    assert verdict("It depends on the feature.") == "conditional"
    assert verdict("The pool must support graphics.") == "none"
