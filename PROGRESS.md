# Progress

Last updated: 2026-11-10. Plan stages refer to `PLAN.md` §4; checkpoints to `PLAN.md` §5.

## Status by stage

| Stage | Status | Notes |
|---|---|---|
| 0. Environment | **done** (except the phase L layout) | uv/Python 3.11, Docker, Ollama on GPU, OpenRouter verified, `ml` extra installed, VRAM measured, BM25 tokenizer tests pass |
| 1. Ingest and corpus | **done** | coverage 100%, corpus hash `5e83355c…` |
| 2. Strata | **done** | cutoff 2024-09-30 (both models), main 400 + pilot 45 frozen (`samples.json` `e63d2b5e…`) |
| 3. Questions | **pilot done (3a + 3b)** | `pilot_questions.jsonl` (95: 90 + 5 unanswerable), gold final, sha256 `094b8a26…` |
| 4. Indexes | **done** | BM25 + bge-m3 dense/sparse over 36,757 chunks, `data/processed/index/` |
| 5. Retrieval | **pilot done** | `runs/pilot/`; checkpoint §5.3 passed |
| 6. Generation | **pilot done** | `runs/pilot/answers.jsonl`, 1,180 answers |
| 7. Evaluation | **pilot done** | judge, metrics, power; judge kappa 0.89 (80 human labels, revised) |
| 8. Report | not started (next session) | pilot = final run; see Hypotheses and Next steps |

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

## Stage 6 — pilot (`vkrag generate`, `runs/pilot/answers.jsonl`)
- 50 questions in generation (45 answerable + 5 unanswerable) x 12 configurations (9 main + controls
  `rrf_rerank_strict`, `rrf_rerank_k3`, `rrf_rerank_k10`) x 2 answerers = 1,180 answers; oracle* skipped for unanswerable.
- Prompts `generation/prompts/answer_{closed,rag,strict}.md`; context format of §9.3.
- qwen: 590 answers in 66 min (5.5 s mean), 100% GPU, max prompt 6,384 tokens (< 8192 - 512). The local
  count (transformers chat template, thinking off) equals Ollama `prompt_eval_count` exactly.
  101 attempts hit num_predict 512 and were retried with 1024; **29 answers still truncated -> missing
  (4.9%; closed 18%)**. Cause: with think=false qwen reasons in the answer ("Let's reconsider...") and
  does not finish. One rerun of a truncated answer finished (682 tokens): qwen on Ollama is not fully
  deterministic at temperature 0.
  Re-run of the 29 (`--retry-missing --start-limit 2048 --max-limit 4096`, 15 min): 25 finished
  (18 of them under 1,100 tokens: truncation was partly chance), **4 still missing at 4096**
  (closed 2, rewrite_rrf_rerank 1, rrf_rerank_k3 1; 0.7%). Judged 2026-11-10 (43 calls, $0.147, 0 failed): qwen closed unchanged (0.278; the 8 re-generated closed answers all scored incorrect), qwen rrf 0.74 -> 0.767, rrf_rerank 0.67 -> 0.70; tables above are pre-rerun, current ones in `runs/pilot/generation_metrics.json`.
- remote `deepseek/deepseek-v4-flash-0731` via **`cohere/fp8`** (DeepInfra returned 429 on every call;
  probe of 12 bf16/fp8 endpoints in `reports/remote_provider_probe.json`): 589/590, $0.148, 16 min.

## Stage 7 — pilot (`vkrag judge`, `runs/pilot/{judgments,scores}.jsonl`, `generation_metrics.json`)
- Judge `google/gemini-3.8-flash` @ `google-ai-studio`, prompts `judge_{correctness,faithfulness}.md`,
  8 parallel workers; 2,172 calls, 0 failures, $4.84 (correctness $0.0016, faithfulness $0.0029 per call).
- Masking (`eval/masking.py`, applied to a fixed point) extended by the pilot leaks; residual markers
  remain in ~10% of RAG answers (`python -m vkrag.eval.mask_audit`) -> limitation for the report.
- Automatic checks `eval/autocheck.py`; identifiers copied from the question are not fabrications.
- Answerable questions, score (correct share), n = 45 per cell:

  | config | qwen | remote |
  |---|---|---|
  | closed | 0.28 (0.18) | 0.50 (0.42) |
  | oracle | 0.96 (0.93) | 0.94 (0.91) |
  | oracle_distract | 0.92 (0.89) | 0.97 (0.96) |
  | bm25 | 0.68 (0.58) | 0.79 (0.73) |
  | dense | 0.76 (0.69) | 0.73 (0.67) |
  | rrf | 0.74 (0.67) | 0.82 (0.76) |
  | rrf_rerank | 0.67 (0.60) | 0.84 (0.78) |
  | rewrite_rrf_rerank | 0.69 (0.64) | 0.79 (0.71) |
  | hyde_rrf_rerank | 0.64 (0.56) | 0.80 (0.76) |
  | rrf_rerank_strict | 0.60 (0.51), abstain 0.13 | 0.61 (0.53), abstain 0.20 |
  | rrf_rerank_k3 / k10 | 0.63 / 0.74 | 0.83 / 0.78 |

- closed-book: fabricated VUID 76% (qwen) / 84% (remote), citation accuracy ~0; hallucination 0.73 / 0.52.
- Remote cost per answerable question: closed $0.000097 (291 output tokens), rrf_rerank $0.000318;
  cost per correct closed $0.000195 < rrf_rerank $0.000376 (**H5 direction not seen on the pilot**).
- Judge length bias: Spearman score vs answer length |rho| > 0.3 in 16 cells, all but one negative
  (longer answers score lower). On the tune labels the human scores show the same trend
  (rho(len, human) -0.73, rho(len, judge) -0.71, rho(len, judge - human) 0.11): long answers are
  worse, the judge is not length-biased.
- Calibration export: `runs/pilot/annotations/judge_calibration_{tune,heldout}.csv` (40 + 40; qwen 38,
  remote 42), key in `judge_calibration.key.jsonl`.
- Tune labels (user, `judge_calibration_tune_annotated.csv` -> `.labels.jsonl`, 40 items): correctness
  weighted kappa 0.881 [0.699, 1.0], agreement 0.925; abstained kappa 1.0; hallucination kappa 0.867
  [0.652, 1.0], agreement 0.95. All 3 correctness disagreements are human partial vs judge correct
  (judge slightly lenient on a right verdict with a wrong detail); 2 hallucinations missed by the judge.
  Mean score human 0.775 vs judge 0.812. Rubric not changed.
- Held-out labels (user, 40 items, rubric unchanged after tune). Blind first pass: correctness weighted
  kappa 0.825 [0.634, 0.957], hallucination kappa 0.658 [0.342, 0.908]. **Revised by the user after
  seeing the disagreement list** (5 label changes on 3 items: Ja9d9acf1 and J4c020d01 correct ->
  partial + hallucination -> true, both towards the judge; Jed28095a hallucination -> true, away from
  the judge; tune: comments only). Revised: correctness kappa 0.897 [0.755, 1.0], agreement 0.925;
  hallucination kappa 0.749 [0.478, 0.944], agreement 0.9; abstained: no human abstention, agreement
  1.0. Mean human 0.750 vs judge 0.738; rho(len, judge - human) 0.16. Pooled 80 (revised):
  correctness kappa 0.890 [0.785, 0.965], hallucination 0.806 [0.641, 0.937], abstained 1.0; human
  mean 0.7625, 22 hallucinations. The held-out set is no longer fully blind: the report gives the
  blind first-pass kappa as the primary held-out estimate and the revised one next to it.

## Power (`vkrag power`, `runs/pilot/power.json`; 2,000 simulations, alpha 0.05/8)
Historical: computed for the cancelled main run. MDE at the pilot size is in the Hypotheses section.
| test | pilot difference | main n | MDE (power >= 0.8) |
|---|---|---|---|
| H1a qwen rrf_rerank - closed | +0.42 | 400 | 0.15 |
| H1b remote rrf_rerank - closed | +0.36 | 400 | 0.13 |
| H2a rrf - bm25 (class@5) | +0.03 | 800 | 0.05 |
| H2b rrf - dense (class@5) | +0.03 | 800 | 0.04 |
| H3a rrf_rerank - rrf (class@5) | -0.19 | 800 | 0.08 |
| H3b rrf_rerank - rrf (score, both) | -0.02 | 800 | 0.09 |
| H4 NI qwen rrf_rerank vs remote closed, margin -0.05 | +0.18 | 400 | P(confirm NI at true diff 0) = **0.29** |

## Budget
- Key usage $6.91 of $11 credits -> $4.09 left; then judging the 25 re-generated qwen answers $0.147
  -> **~$3.94 left** (2026-11-10).
- Spent on 2026-11-07/08: cutoff probe + checks $0.52, Stage 3b $0.93.
- Stage 6-7 pilot (approved $3.3 + $1.25 for the controls): judge $4.84 + probes/stopped runs ~$0.1,
  remote answers $0.148, provider probe ~$0.03 -> ~$5.5 (**~$0.9 over the approval**).
- (Cancelled) main run extrapolation (PLAN §9.1 counts, pilot per-call costs): remote $1.2, judge correctness $14.8,
  faithfulness $18.5 -> ~$35, with 30% reserve **~$45**; qwen ~8 h.

## Hypotheses (final = pilot run, exploratory)
`uv run vkrag hypotheses` -> `runs/pilot/hypotheses.json` (~45 s). Paired by question, clustered by
entity; cluster bootstrap 95% CI (10k), cluster sign-flip permutation p (10k), Holm over the 8 tests
for reference. Generation: 45 answerable questions (40 entities); retrieval: 90.

| test | A -> B | diff [95% CI] | p | p_Holm | reading |
|---|---|---|---|---|---|
| H1a qwen rrf_rerank vs closed (score) | 0.278 -> 0.700 | +0.422 [0.277, 0.558] | 0.0001 | 0.0008 | supported |
| H1b remote rrf_rerank vs closed | 0.500 -> 0.844 | +0.344 [0.198, 0.479] | 0.0003 | 0.0021 | supported |
| H2a rrf vs bm25 (class@5) | 0.689 -> 0.722 | +0.033 [-0.023, 0.089] | 0.45 | 1.0 | no difference |
| H2b rrf vs dense (class@5) | 0.689 -> 0.722 | +0.033 [-0.011, 0.081] | 0.38 | 1.0 | no difference |
| H3a rrf_rerank vs rrf (class@5) | 0.722 -> 0.533 | -0.189 [-0.290, -0.087] | 0.001 | 0.007 | opposite: reranker hurts |
| H3b rrf_rerank vs rrf (score, both) | 0.794 -> 0.772 | -0.022 [-0.128, 0.080] | 0.76 | 1.0 | no difference; latency not measured |
| H4 qwen rrf_rerank - remote closed | 0.500 vs 0.700 | +0.200 [0.023, 0.372] | NI 0.003 | 0.013 | NI holds (margin -0.05) |
| H5 remote cost_per_correct rrf_rerank vs closed | $0.000195 -> $0.000376 | +$0.000181 [0.000057, 0.000276] | 0.001 | 0.007 | opposite: RAG costs more per correct |

- H5: cost_per_question +$0.000220 [0.000175, 0.000260] (as expected), but cost_per_correct is also
  higher: remote closed answers are cheap enough that the accuracy gain does not pay for the context.
- Binary sensitivity (correct = 1): H1a +0.42 (p 0.0003), H1b +0.36 (p 0.001), H3b -0.03, H4 +0.18
  [-0.024, 0.367] (NI still holds).
- MDE at the pilot size (binary, power 0.8; alpha 0.05 / alpha 0.05/8): H1a 0.35/0.44, H1b 0.30/0.37,
  H2a/H2b 0.13/0.18, H3a/H3b 0.20/0.25 (high discordance: 0.73 for H1a).
- Exploratory: H1 DiD (rrf_rerank - closed, recent+ext_niche vs core_1_0): qwen +0.36 [-0.09, 0.80],
  remote +0.17 [-0.21, 0.50] (18 vs 9 questions). H2 interaction (rrf - bm25, descriptive - identifier):
  +0.11 [0.0, 0.22] (45 pairs). Retrieval loss (oracle - rrf_rerank): qwen +0.26 [0.16, 0.37], remote
  +0.10 [0.0, 0.20].

## Open questions for the user
1. Checkpoint §5.1: review of `reports/stage1_samples.md` (optional; otherwise a limitation).

Resolved 2026-11-10: phase L, repeats, `oracle_entity` dropped; H1-H5 exploratory; no main run
(budget); judge calibration done; held-out reported blind first + revised; report = `reports/report.md`
+ notebook.

## Next steps
The pilot is the final run (no main run; PLAN §10, 2026-11-10). Calibration, re-generation and the
hypothesis tests are done.
1. Stage 8: `reports/report.md` (English) + notebook with figures (PLAN Stage 8 tables 0-3, strata
   plot, Pareto score vs cost, limitations: exploratory status, pilot-tuned masking/autochecks,
   held-out labels revised after the disagreement list, qwen nondeterminism, no latency/phase L,
   no repeats, no `oracle_entity`).
2. Optional: checkpoint §5.1 review of `reports/stage1_samples.md` (else a limitation).

Tests: 120 passing.
