"""Near-duplicate questions by bge-m3 cosine (PLAN §4 Stage 3). The two styles of the same VU are
paraphrases by design, so pairs with the same vuid are not compared."""

from __future__ import annotations


def near_duplicates(recs: list[dict], threshold: float) -> dict:
    from vkrag.index.embed import encode

    qs = [r for r in recs if isinstance(r.get("question"), str)]
    if len(qs) < 2:
        return {"threshold": threshold, "pairs": [], "top": []}
    v = encode([r["question"] for r in qs])
    sim = v @ v.T
    pairs = []
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            if qs[i].get("vuid") and qs[i].get("vuid") == qs[j].get("vuid"):
                continue
            pairs.append((float(sim[i, j]), qs[i]["qid"], qs[j]["qid"]))
    pairs.sort(reverse=True)
    same_vu = [
        float(sim[i, j])
        for i in range(len(qs))
        for j in range(i + 1, len(qs))
        if qs[i].get("vuid") and qs[i].get("vuid") == qs[j].get("vuid")
    ]
    return {
        "threshold": threshold,
        "pairs": [{"cos": round(s, 4), "a": a, "b": b} for s, a, b in pairs if s >= threshold],
        "top": [{"cos": round(s, 4), "a": a, "b": b} for s, a, b in pairs[:20]],
        "same_vu_style_pairs": sorted(round(x, 4) for x in same_vu),  # calibration: known paraphrases
    }
