from vkrag.eval.masking import mask


def test_vuids_masked():
    t, m = mask("Not allowed (VUID-vkCmdDraw-None-02700). See vkCmdResetEvent2-stageMask-03929.")
    assert "02700" not in t and "03929" not in t and t.count("[VUID]") == 2 and not m


def test_context_markers_removed():
    cases = [
        "According to the provided context, the pool must support graphics.",
        "Based on the context above, the pool must support graphics.",
        "The context does not mention this case. The pool must support graphics.",
        "As stated in [2], the pool must support graphics.",
        "The pool must support graphics (see context [1]).",
    ]
    for c in cases:
        t, m = mask(c)
        assert m, c
        assert "context" not in t.lower() and "[1]" not in t and "[2]" not in t, t
        assert "pool must support graphics" in t


def test_remaining_context_mentions_neutralized():
    s = ("Based on the provided context, here is the analysis: The context explicitly states in **[2]** that X. "
         "The provided text for vkCmdResetEvent2 (**[1]**) does not list it. While the provided context snippet cites Y.")
    t, m = mask(s)
    assert m and "context" not in t.lower() and "provided" not in t.lower() and "**" not in t, t
    assert t.startswith("Here is the analysis")


def test_pilot_residual_markers():
    cases = [
        "(The specification does not contain the answer. I am relying on my own knowledge as permitted by the instructions.)",
        "However, looking at **Snippet [3]**, it defines a VUID for 1D images.",
        "Note: this VUID in your context text refers to 1D images.",
        "Note: The provided [1], [2] and describe the indirect count command.",
        "The API specification provided does not explicitly enforce this.",
    ]
    for c in cases:
        t, m = mask(c)
        assert m, c
        low = t.lower()
        assert not any(w in low for w in ("knowledge", "instructions", "snippet", "context", "provided")), t


def test_ordinary_context_word_kept():
    s = "Using geometry shaders in a graphics context requires the feature."
    assert mask(s) == (s, False)


def test_own_knowledge_marker():
    t, m = mask("Yes. From my own knowledge, this is allowed.")
    assert m and "knowledge" not in t and t.startswith("Yes.")


def test_plain_answer_untouched():
    s = "No. srcStageMask must not include VK_PIPELINE_STAGE_HOST_BIT."
    assert mask(s) == (s, False)


def test_section_markers_from_pilot():
    for s in ["**Relevant VUIDs (from context):** [VUID]", "**Relevant VUIDs from context:** none",
              "1. **Context Analysis**: the rule applies.", "**VUID:** `[VUID]` **Rule:** ` (VU) [VUID]`",
              "According to the VUIDs provided, it is invalid.", "This matches [VUID] (Section in context)."]:
        t, m = mask(s)
        assert m and "context" not in t.lower() and "provided" not in t and "(VU)" not in t, t


def test_fixed_point_and_general_knowledge():
    for s in ["Consistent with the context provided, x must be y.",
              "**Relevant VUIDs (from general spec knowledge, not in context):** none.",
              "The Vulkan specification text provided does not say."]:
        t, m = mask(s)
        assert m and "provided" not in t and "context" not in t.lower() and "knowledge" not in t, t
