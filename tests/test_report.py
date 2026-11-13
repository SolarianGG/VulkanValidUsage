import numpy as np

from vkrag.report import _md, cluster_mean_ci


def test_cluster_mean_ci_weights_questions_not_clusters():
    rng = np.random.default_rng(0)
    rows = [("a", 1.0), ("a", 1.0), ("a", 1.0), ("b", 0.0)]
    d = cluster_mean_ci(rows, 2000, rng)
    assert d["mean"] == 0.75 and d["n"] == 4 and d["clusters"] == 2
    lo, hi = d["ci95"]
    assert lo == 0.0 and hi == 1.0  # resampling two clusters can give all-a or all-b


def test_cluster_mean_ci_constant():
    d = cluster_mean_ci([(str(i), 1.0) for i in range(10)], 500, np.random.default_rng(1))
    assert d["mean"] == 1.0 and d["ci95"] == [1.0, 1.0]


def test_cluster_mean_ci_empty():
    assert cluster_mean_ci([], 10, np.random.default_rng(0))["mean"] is None


def test_md_table():
    assert _md(["a", "b"], [[1, 2]]) == ["| a | b |", "|---|---|", "| 1 | 2 |", ""]
