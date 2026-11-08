# Progress

Last updated: 2026-11-08. Plan stages refer to `PLAN.md` §4; checkpoints to `PLAN.md` §5.

## Status by stage

| Stage | Status | Notes |
|---|---|---|
| 0. Environment | **done** (except the phase L layout) | uv/Python 3.11, Docker, Ollama on GPU, OpenRouter verified, `ml` extra installed, VRAM measured, BM25 tokenizer tests pass |
| 1. Ingest and corpus | **done** | coverage 100%, corpus hash `5e83355c…` |
| 2. Strata | **done** | cutoff 2024-09-30 (both models), main 400 + pilot 45 frozen (`samples.json` `e63d2b5e…`) |
| 3. Questions | **pilot done (3a + 3b)** | `pilot_questions.jsonl` (95: 90 + 5 unanswerable), gold final, sha256 `094b8a26…` |
| 4. Indexes | **done** | BM25 + bge-m3 dense/sparse over 36,757 chunks, `data/processed/index/` |
| 5. Retrieval | **pilot done** | `runs/pilot/`; checkpoint §5.3 passed |
| 6–8 | not started | |

## Stage 0 — what was verified
- Spec tag `v1.4.366` (freeze 2026-11-07), image `khronosgroup/docker-images@sha256:f1ca671f…4762`.
- Ollama 0.40.15 was CPU-only because of a broken install; fixed by reinstalling. The original
  `qwen3.5:9b` ran 12%/88% CPU/GPU because of its vision projector, so the text-only variant
  `qwen3.5-9b-text` was created (`configs/ollama/qwen3.5-9b-text.Modelfile`): 100% GPU, 59 tok/s.
- `think=false` is honored; `keep_alive=0` frees VRAM (7.5 → 1.2 GB).
- `ml` extra: torch 2.6.0+cu124, sentence-transformers 6.2.0, FlagEmbedding, faiss-cpu 1.15.1.
- VRAM (nvidia-smi, MB of 8192): Windows alone 1,945; + bge-m3 fp16 3,360 (3,725 after a 256-chunk
  batch, torch peak 1.4 GB); + bge-reranker-v2-m3 fp16 4,734 after 50 pairs at max_length 1024
  (torch peak 2.4 GB). qwen with num_ctx 8192 takes ~5 GB over the baseline (6.6 GB total).
  **Conclusion:** embedder and reranker fit together, but not next to qwen (~9.8 GB). Offline phases
  run as separate processes; phase L needs a decision (see open questions).
- Speed: bge-m3 256 chunks 3.9 s; reranker 50 pairs 1.9 s (GPU, fp16).

## Stage 1 — results
- `validusage.json` (schema v2): 27,429 VUs (20,575 explicit / 6,854 implicit), identical to the
  Vulkan-Headers copy. All conditions are `core`, so the extension conditions were rebuilt from
  adoc `ifdef`s: 20,575/20,575 explicit VUIDs, exact match.
- Registry: 1,263 aliases, 3,745 entities, 479 extensions, 16,902 identifiers over 335 tags + main.
- Sections: 3,101 refpage + 4,695 prose units. Chunks: 4,027 refpage parts, 5,301 prose parts,
  27,429 VU chunks. Section parts ≤ 797 tokens (max over the qwen / XLM-R / DeepSeek tokenizers).
- Equivalence classes: suffix + identical raw text (placeholder rejected): 7,261 explicit
  classes, largest 40.
- Details: `reports/data_facts.md`; manual review sample: `reports/stage1_samples.md`.

## Stage 2 — results
- `vuid_history.json`: 97 tags (v1.3.269 baseline … v1.4.366, `v1.4.308` has no Headers json).
- gpuinfo snapshot (Recent 1y, Windows + Linux, combine rule `platform`), instance extensions included.
- Cutoff probe variant (a): DeepSeek cutoff 2024-09-30; qwen undetermined; user decision: 2024-09-30
  for both, sensitivity 2024-06-30 / 2024-12-31 / 2025-03-31.
- Final strata: recent 5,184 / ext_niche 7,907 / ext_popular 2,484 / core_promoted 2,264 / core_1_0 1,633 eligible;
  main 400 (244 entities) + pilot 45 frozen; `reports/strata_table.md`.
- Details: `reports/data_facts.md` (section "Stage 2 inputs").

## Stage 3 — so far
- SPIR-V/GLSL dictionary `data/external/spirv_identifiers.txt` (`vkrag spirv`): 3,603 names
  (SPIRV-Headers `fbf86836` 2026-10-21, GLSL `0099bf83`), meta in `spirv_identifiers.meta.json`.
- BM25 tokenizer `index/tokenize.py` (identifiers whole + parts, stop words, Snowball stemming of
  words and parts); n-gram leak filter on unstemmed content words without identifiers.
- `vkrag questions prepare --sample pilot`: 45 VUs → 7 batches (1–12 items, 170–410k chars of JSON
  each, ~45–100k tokens) in `data/questions/generation_log/batches/pilot/`; batch_unans (quotas 2/2/1).
  Assignments (`pilot_assignments.json`): answer_type 3/3/3 per stratum (15/15/15 overall, target
  40/30/30 is unreachable with 9 per stratum), verdicts 8 yes / 7 no, gen_style 23 identifier / 22 descriptive.
- Generator context per VU: parent section, all VUs of the entity and of one level of related
  structures (vk.xml param/member types + pNext extenders), up to 6 ref chunks; identical VU texts
  in a batch are shown once (`same_text_as`).
- `vkrag questions validate`: schema, qid/style matching, answer_type/verdict consistency, coverage of
  `checked_entities`/`checked_vuids`, `also_relevant_vuids` empty, n-gram ≤ 5, identifiers in
  descriptive questions, VUID mentions, unanswerable existence check, bge-m3 near-duplicates
  (+ cosine of the same-VU style pairs for threshold calibration).
- Pilot generated 2026-11-07 by 8 Claude Code subagents (`claude-opus-5-5`, one per batch, self-check
  with `validate --no-dedup`, prompt_v1); run log with input/output hashes in `generation_log/pilot_runs.json`.
- User review 2026-11-08: questions accepted. Stricter n-gram filter approved (reject if the n-gram
  without or with stop words is > 5); it rejected one near-verbatim question (qp-447f14a302-id),
  regenerated in batch 008 with `prompt_v2` (`questions prepare --regen`; validate keeps the latest batch per VU).
- `prompt_v2.md` (for the main set): n-gram rule counts small words, `stratum` in the unanswerable
  template, unanswerable references only from the batch text. prompt_v1 is unchanged (hash in pilot_runs.json).
- Validator fixes: unit symbols are not identifiers; a 5-digit number is a VU-number leak only if
  it is a suffix of a VU of the target entity.
- Cosine (bge-m3): same-VU style pairs 0.59-0.83; different-VU pairs max 0.87; threshold 0.92 kept.
- `vkrag questions freeze --sample pilot`: `data/questions/pilot_questions.jsonl` + manifest; 50 questions
  `in_generation` (45 VUs, one style each: 23 identifier / 22 descriptive) + 5 unanswerable;
  graded gold (3 gold VU / 2 class / 1 parent section parts and ref sections); 64 of 90 have a
  multi-VU class, largest 39; `gold_final: false` until Stage 3b.

## Stage 4 — results
- `vkrag index`: BM25 (bm25s 0.3.16, lucene, k1 1.2, b 0.75, vocab 24,719, 6 s); bge-m3 dense
  (FAISS IndexFlatIP, 1024-d, normalized) + sparse lexical weights (CSR, 60 nnz/chunk) in one pass, 217 s.
- Model revisions pinned in the config: bge-m3 `5617a9f6…`, reranker `953dc6f6…`; the embedder is
  `FlagEmbedding.BGEM3FlagModel` everywhere (index, queries, question dedup).

## Stage 5 — pilot results (`runs/pilot/`, 90 answerable questions)
- Phase A (`vkrag transform`): 190 qwen calls, median latency rewrite 0.45 s / HyDE 2.1 s, 100% GPU,
  VRAM freed afterwards; non-existent vk identifiers in 16% of rewrites, 22% of HyDE passages;
  one rewrite degenerated into a repetition loop up to num_predict (qp-372fd8f17a-id).
- Phase B (`vkrag retrieve --configs all`): 15 configurations, metrics in `retrieval_metrics.json`.
  Equivalence classes are collapsed inside every retriever (raw depth 2,000 -> 50 distinct classes) and
  RRF fuses by class (user decision 2026-11-08). Earlier runs kept as `retrieved.no_collapse.jsonl`
  and `retrieved.collapse_chunk_rrf.jsonl` (RRF by chunk split the votes of a class: class@5 0.48).

  | config | class@1 | class@5 | class@20 | mrr@10 | ndcg@10 | class@5 id / desc |
  |---|---|---|---|---|---|---|
  | bm25 | 0.433 | 0.689 | 0.811 | 0.548 | 0.473 | 0.84 / 0.53 |
  | dense | 0.500 | 0.689 | 0.778 | 0.585 | 0.398 | 0.84 / 0.53 |
  | sparse | 0.200 | 0.311 | 0.467 | 0.249 | 0.221 | |
  | rrf | 0.478 | 0.722 | 0.833 | 0.585 | 0.458 | 0.82 / 0.62 |
  | rrf_rerank | 0.300 | 0.533 | 0.744 | 0.408 | 0.369 | 0.71 / 0.36 |
  | hyde_rrf | 0.522 | 0.722 | 0.856 | 0.607 | 0.475 | 0.82 / 0.62 |
  | rewrite_rrf | 0.389 | 0.667 | 0.811 | 0.525 | 0.406 | |
  | oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.878 | |

- Reranker hurts (kept as a result for H3, user decision): it lifts section chunks (VU share in
  the context 0.71 for rrf vs 0.42 for rrf_rerank).
- Checkpoint §5.3: oracle strict recall 100%; no contexts shorter than k; no duplicate class in a
  context; thinking off; transform prompts tiny.

## Stage 3b — pilot (`vkrag acceptable`)
- Judge `google/gemini-3.8-flash` (Google AI Studio, reasoning medium), prompt
  `generation/prompts/judge_acceptable.md`; top-10 out-of-class VU chunks of `rrf_rerank` per question.
- 900 verdicts, $0.926 (441 prompt / 139 completion tokens per call, ~$0.001 per call);
  **0 equivalent**. The 79 candidates with near-identical text (fuzz >= 90) are genuinely different
  rules (RTE vs RTZ, opposite NULL condition, synchronization1 vs 2 command) and the reasons are correct.
  Gold is final (`gold_final: true`, manifest stage 3b).
- Tests: 92 passing.

## Budget
- Spent on 2026-11-07/08: cutoff probe ~$0.15 + checks ~$0.37 (key usage $0.52 on 2026-11-07), 3b $0.93.
- Stage 6-7 pilot estimate (50 questions in generation, 9 configurations, 2 answerers):
  remote answerer 440 calls ~$0.07; judge 880 correctness + 780 faithfulness ~$3.2. Total ~$3.3.

## Open questions for the user
1. Checkpoint §5.1: review of `reports/stage1_samples.md` (not done).
2. Approval of the Stage 6-7 pilot budget (~$3.3 of the remaining ~$8.5).
3. Phase L layout: deferred to Stage 6 by the user.

## Next steps
Pilot (checkpoint §5.4), after the budget approval:
1. Stage 6 code: answerer prompts (`generation/prompts/answer_*.md`: closed, RAG, strict), context
   format of §9.3, `vkrag generate` (phase C) for qwen (local prompt-token check with the chat
   template, `prompt_tokens + num_predict <= num_ctx`) and the remote answerer; usage log
   `runs/<id>/usage.jsonl`; skip policy (3 retries, then `missing`).
2. Stage 7 code: answer masking (`eval/masking.py` with tests), judge prompts (correctness,
   faithfulness), `vkrag judge` (phase D), automatic checks (fabricated / outdated identifiers).
3. Run the pilot: 50 questions in generation x 9 configurations x 2 answerers (`--dry-run` first).
4. Judge calibration: `vkrag annotate export|import` (40/40 split), user labels, kappa.
5. Extrapolate time and OpenRouter cost of the full run; power analysis (`vkrag power`);
   fix PLAN §7.5 (comparisons, family size, thresholds, margins) before the full run.

Main run (checkpoint §5.5):
6. `vkrag questions prepare --sample main` (400 VUs, prompt_v2), generation by subagents,
   `validate`, 50 unanswerable, user review of 80 pairs, `freeze`, Stage 3b on main.
7. Phases A-D on main, repeats (3 runs on 100 questions), phase L (layout decision pending).
8. Stage 8: report (`reports/report.md`, notebook).
