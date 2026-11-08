import math

from vkrag.eval.retrieval_metrics import metrics_for
from vkrag.retrieval import core


def test_rrf_order_and_ties():
    a = [("x", 9.0), ("y", 8.0), ("z", 7.0)]
    b = [("y", 0.9), ("w", 0.8)]
    r = core.rrf([a, b], 60, 10)
    assert [d for d, _ in r][:2] == ["y", "x"]  # y appears in both lists
    assert math.isclose(dict(r)["y"], 1 / 62 + 1 / 61)
    assert len(core.rrf([a, b], 60, 2)) == 2


class FakeCorpus:
    def __init__(self):
        self.chunks = {
            "VUID-A-1": {"type": "vu", "equiv_class_id": "eq1", "llm_text": "VUID-A-1\nrule one"},
            "VUID-B-1": {"type": "vu", "equiv_class_id": "eq1", "llm_text": "VUID-B-1\nrule one"},
            "VUID-C-2": {"type": "vu", "equiv_class_id": "eq2", "llm_text": "VUID-C-2\nrule two"},
            "sec-1": {"type": "section", "llm_text": "section text"},
            "sec-2": {"type": "section", "llm_text": "section text"},
        }
        self.alias_to_target = {"vkCmdBeginRenderingKHR": "vkCmdBeginRendering"}
        self.target_to_aliases = {"vkCmdBeginRendering": ["vkCmdBeginRenderingKHR"]}

    alias_names = core.Corpus.alias_names


def test_assemble_context_dedups_class_and_text():
    ranked = [("VUID-A-1", 1), ("VUID-B-1", 1), ("sec-1", 1), ("sec-2", 1), ("VUID-C-2", 1)]
    assert core.assemble_context(ranked, FakeCorpus(), 5) == ["VUID-A-1", "sec-1", "VUID-C-2"]
    assert core.assemble_context(ranked, FakeCorpus(), 2) == ["VUID-A-1", "sec-1"]


def test_collapse_keeps_best_member_per_class():
    ranked = [("VUID-A-1", 3), ("VUID-B-1", 2), ("sec-1", 1.5), ("VUID-C-2", 1), ("sec-2", 0.5)]
    assert [d for d, _ in core.collapse(ranked, FakeCorpus(), 10)] == ["VUID-A-1", "sec-1", "VUID-C-2", "sec-2"]
    assert [d for d, _ in core.collapse(ranked, FakeCorpus(), 2)] == ["VUID-A-1", "sec-1"]


def test_bm25_alias_expansion_both_directions():
    s = core.Searchers.__new__(core.Searchers)
    s.c = FakeCorpus()
    toks = s.bm25_query_tokens("Can vkCmdBeginRenderingKHR be used?")
    assert "vkcmdbeginrenderingkhr" in toks and "vkcmdbeginrendering" in toks
    toks = s.bm25_query_tokens("vkCmdBeginRendering")
    assert "vkcmdbeginrenderingkhr" in toks


def test_family_prefix():
    assert core._family("vkCmdDrawIndexedIndirect") == "vkCmdDraw"
    assert core._family("VkImageCreateInfo") == "VkImage"


def test_metrics_for():
    q = {"vuid": "VUID-A-1", "gold_chunk_ids": {"VUID-A-1": 3, "VUID-B-1": 2, "sec-1": 1}}
    m = metrics_for(["sec-1", "VUID-B-1", "x"], q, {"sec-1"}, [1, 3])
    assert m["strict@3"] == 0 and m["class@1"] == 0 and m["class@3"] == 1 and m["soft@1"] == 1
    assert m["mrr@10"] == 0.5
    assert 0 < m["ndcg@10"] < 1
    perfect = metrics_for(["VUID-A-1", "VUID-B-1", "sec-1"], q, {"sec-1"}, [1])
    assert math.isclose(perfect["ndcg@10"], 1.0)


def test_rrf_fuses_members_of_one_class():
    fc = FakeCorpus()
    a = [("VUID-A-1", 1.0), ("VUID-C-2", 0.5)]
    b = [("VUID-B-1", 1.0), ("VUID-C-2", 0.5)]
    r = core.rrf([a, b], 60, 10, core.class_key(fc))
    assert [d for d, _ in r] == ["VUID-A-1", "VUID-C-2"]  # A-1 and B-1 share eq1, votes summed
    assert math.isclose(dict(r)["VUID-A-1"], 2 / 61)


def test_collapsed_ideal():
    from vkrag.eval.retrieval_metrics import collapsed_ideal

    fc = FakeCorpus()
    gold = {"VUID-A-1": 3, "VUID-B-1": 2, "sec-1": 1}
    assert sorted(collapsed_ideal(gold, fc.chunks)) == [1, 3]
