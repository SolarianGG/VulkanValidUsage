import numpy as np

from vkrag.eval import hypotheses as H


def test_holm():
    assert H.holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06}
    assert H.holm({"a": 0.5, "b": 0.9}) == {"a": 1.0, "b": 1.0}


def test_paired_effect_ci_and_p():
    rng = np.random.default_rng(0)
    rows = [(f"e{i // 2}", 0.0, 1.0) for i in range(40)]  # B always better, 20 clusters of 2
    r = H.paired(rows, 2000, 2000, rng)
    assert r["diff"] == 1.0 and r["ci95"] == [1.0, 1.0] and r["p"] < 0.001 and r["entities"] == 20
    rows = [(f"e{i}", float(i % 2), float(1 - i % 2)) for i in range(40)]  # no effect
    r = H.paired(rows, 2000, 2000, rng)
    assert r["diff"] == 0.0 and r["p"] > 0.5 and r["ci95"][0] < 0 < r["ci95"][1]


def test_cost_test_ratio():
    rng = np.random.default_rng(0)
    a, b = ("m", "closed"), ("m", "rag")
    sc = {f"q{i}": {"entity": f"e{i}", a: {"cost_usd": 1.0, "score": 0.5}, b: {"cost_usd": 2.0, "score": 1.0}} for i in range(20)}
    r = H.cost_test(sc, a, b, 500, 500, rng)
    assert r["cost_per_question"]["diff"] == 1.0 and r["cost_per_correct"]["a"] == 2.0
    assert r["cost_per_correct"]["diff"] == 0.0


def test_did_paired():
    rng = np.random.default_rng(0)
    rows = [(f"e{i}", 1.0, 0.0) for i in range(10)]
    r = H.did_paired(rows, 500, rng)
    assert r["did"] == 1.0 and r["pairs"] == 10
