from collections import Counter

from vkrag.eval.annotate import cohen_kappa, select


def test_kappa_values():
    cats = ["correct", "partial", "incorrect"]
    a = ["correct", "partial", "incorrect", "correct"]
    assert cohen_kappa(a, a, cats, weighted=True) == 1.0
    # one adjacent disagreement is penalized less by the linear weights
    b = ["correct", "correct", "incorrect", "correct"]
    assert cohen_kappa(a, b, cats, weighted=True) > cohen_kappa(a, b, cats, weighted=False)
    assert round(cohen_kappa([True, False, True, False], [True, False, False, True], [True, False]), 3) == 0.0


def test_select_round_robin_cells():
    qs = {f"q{i}": {"stratum": ["recent", "core_1_0"][i % 2], "answer_type": "rule"} for i in range(10)}
    answers = [
        {"key": f"{a}{c}{i}", "qid": f"q{i}", "answerer": a, "config": c}
        for a in ("qwen", "remote")
        for c in ("closed", "rrf")
        for i in range(10)
    ]
    s = select(answers, qs, seed=1, n=8)
    assert Counter((x["answerer"], x["config"]) for x in s) == {
        k: 2 for k in [("qwen", "closed"), ("qwen", "rrf"), ("remote", "closed"), ("remote", "rrf")]
    }
    assert Counter(qs[x["qid"]]["stratum"] for x in s) == {"recent": 4, "core_1_0": 4}
