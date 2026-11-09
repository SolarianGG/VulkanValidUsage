"""Phase C: context format, configuration mapping and the skip policy (PLAN Stage 6, §9.3)."""
import io
import json

from vkrag.generation import answer as A

CHUNKS = {
    "VUID-x-1": {"chunk_id": "VUID-x-1", "type": "vu", "title": None, "llm_text": "VUID-x-1\n[vkX] rule one\n"},
    "sec-1": {"chunk_id": "sec-1", "type": "section", "title": "vkX", "llm_text": "[vkX]\nprose"},
}


def test_render_context_format():
    s = A.render_context(["VUID-x-1", "sec-1"], CHUNKS)
    assert s == "[1] (VU)\nVUID-x-1\n[vkX] rule one\n---\n[2] (Section: vkX)\n[vkX]\nprose"


def test_user_message_closed_and_yes_no():
    q = {"question": "Is it valid? ", "answer_type": "yes_no"}
    assert A.user_message(q, None, CHUNKS) == "Is it valid?\n" + A.YES_NO_SUFFIX
    m = A.user_message({"question": "Q", "answer_type": "rule"}, ["sec-1"], CHUNKS)
    assert m.startswith("Context:\n[1] (Section: vkX)") and m.endswith("\n\nQuestion: Q")


def test_source_config_and_prompt_kind():
    assert A.source_config("closed") == (None, None)
    assert A.source_config("rrf_rerank_strict") == ("rrf_rerank", None)
    assert A.source_config("rrf_rerank_k3") == ("rrf_rerank", 3)
    assert A.source_config("hyde_rrf_rerank") == ("hyde_rrf_rerank", None)
    assert [A.prompt_kind(c) for c in ("closed", "rrf", "rrf_rerank_strict")] == ["closed", "rag", "strict"]


class Fake:
    name = "fake"

    def __init__(self, outcomes):
        self.outcomes, self.limits = list(outcomes), []

    def default_limit(self):
        return 100

    def call(self, messages, limit):
        self.limits.append(limit)
        o = self.outcomes.pop(0)
        if isinstance(o, Exception):
            raise o
        return {"content": o[0], "finish_reason": o[1]}


JOB = {"qid": "q", "config": "c", "answerer": "fake", "repeat_idx": 0, "question_hash": "h", "context": None,
       "retrieval_hash": None, "prompt_hash": "p", "messages": []}


def _run(outcomes):
    f, fake = io.StringIO(), Fake(outcomes)
    rec = A.answer_one(fake, JOB, f, "r", backoff_s=0)
    return rec, fake, [json.loads(l) for l in f.getvalue().splitlines()]


def test_errors_retried_three_times_then_missing():
    rec, fake, usage = _run([RuntimeError("x")] * 4)
    assert rec["missing"] and rec["answer"] is None and rec["retries"] == 4 and len(usage) == 4


def test_error_then_success():
    rec, _, usage = _run([RuntimeError("x"), ("Yes.", "stop")])
    assert not rec["missing"] and rec["answer"] == "Yes." and len(usage) == 2


def test_truncation_retried_once_with_doubled_limit():
    rec, fake, _ = _run([("partial", "length"), ("full", "stop")])
    assert rec["answer"] == "full" and fake.limits == [100, 200]
    rec, fake, _ = _run([("", "stop"), ("", "stop")])
    assert rec["missing"] and fake.limits == [100, 200]


def test_rerun_start_and_max_limit():
    fake = Fake([("a", "length"), ("b", "length"), ("c", "length")])
    rec = A.answer_one(fake, JOB, io.StringIO(), "r", backoff_s=0, start_limit=2000, max_limit=4000)
    assert rec["missing"] and fake.limits == [2000, 4000]


def test_config_errors_not_retried():
    rec, fake, _ = _run([A.ContextOverflow("big")])
    assert rec["missing"] and rec["error"].startswith("ContextOverflow") and fake.limits == [100]
