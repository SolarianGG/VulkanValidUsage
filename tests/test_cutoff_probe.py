from vkrag.cutoff_probe import bin_end, bin_of, cutoff_month, month_add


def test_month_add():
    assert month_add("2026-10", -29) == "2024-05"
    assert month_add("2025-12", 1) == "2026-01"


def test_cutoff_rule():
    ms = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
    # last month >= 50% followed by two months < 50%
    assert cutoff_month({"2025-01": 1, "2025-02": 0.6, "2025-03": 0.8, "2025-04": 0.2, "2025-05": 0, "2025-06": 0}, ms) == "2025-03"
    # a later isolated hit followed by two misses moves the cutoff
    assert cutoff_month({"2025-01": 1, "2025-02": 0.2, "2025-03": 0.0, "2025-04": 0.5, "2025-05": 0, "2025-06": 0.1}, ms) == "2025-04"
    # months without data are skipped
    assert cutoff_month({"2025-01": 1, "2025-02": None, "2025-03": 0.1, "2025-04": 0.0}, ms) == "2025-01"
    # no month qualifies when the tail is never two consecutive misses
    assert cutoff_month({m: 1.0 for m in ms}, ms) is None


def test_bins():
    assert bin_of("2025-05", "quarter") == "2025-Q2" and bin_of("2025-05", "month") == "2025-05"
    assert bin_end("2025-Q1") == "2025-03-31" and bin_end("2024-02") == "2024-02-29"
