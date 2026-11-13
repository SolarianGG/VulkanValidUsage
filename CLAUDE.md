# VulkanValidatorAssistant — instructions for Claude Code sessions

Experiment: does RAG over the Vulkan spec beat model memory on Valid Usage (VU) questions?
- `PLAN.md` (Russian) is the source of truth for the design; §10 is the decision log.
- `PROGRESS.md` is the current status: what is done, key numbers, open questions, next steps.
  Read it first, and update it at the end of every work session.
- `reports/data_facts.md` lists verified facts about the data and environment.

## Rules
- **All text in the repository is English**: code, comments, docstrings, configs, CLI help, logs,
  reports (including the final report). Only `PLAN.md` and the chat with the user are Russian.
- When a decision deviates from `PLAN.md`, update the relevant plan section **and** add a row to
  `PLAN.md` §10 (in Russian), then reflect it in `PROGRESS.md`.
- Do not change already approved decisions silently; ask the user.
- Commit only when the user asks.

## Environment (Windows 11, RTX 3070 Laptop 8 GB)
- Python 3.11 via `uv` (`uv run vkrag ...`, tests: `uv run --group dev pytest -q`).
- Shell: prefer the Bash tool. Write Python scripts with the Write tool rather than bash heredocs:
  heredocs here have mangled backslashes (`\b`, `\(`, `\n`) more than once.
- Set `PYTHONIOENCODING=utf-8` when printing spec text (console codepage is cp1251).
- Ollama runs natively; model `qwen3.5-9b-text` (qwen3.5:9b weights without the vision projector),
  host `http://127.0.0.1:11434`. Always pass `temperature=0`, `presence_penalty=0`, `think=false`,
  `num_ctx`, `num_predict`. Check `ollama ps` shows `100% GPU`.
- Spec build: Docker volume `vkdocs-build`, pinned image digest from `BUILD.adoc` of the tag
  (`uv run vkrag spec build`; use `MSYS_NO_PATHCONV=1` for docker commands in Git Bash).
- Heavy ML deps (torch, sentence-transformers, FlagEmbedding, faiss) are the optional `ml` extra
  (installed: torch 2.6.0+cu124, `uv sync --extra ml --group dev`). Models in the HF cache:
  `BAAI/bge-m3`, `BAAI/bge-reranker-v2-m3`.
- Large files: `data/build/vkspec.html` is 41 MB; parse it once (BeautifulSoup+lxml ~15 s) and
  index ids in a dict; never call `soup.find(id=...)` in a loop.

## Pipeline commands (done so far)
```
uv run vkrag spec select-tag   # tag + digest into configs/default.yaml
uv run vkrag spec build        # data/build/{vkspec.html, validusage.json, specattribs.adoc}
uv run vkrag ingest            # registry/aliases/identifiers, adoc VU conditions, vu_base.jsonl
uv run vkrag chunk             # chunks.jsonl, vuids.jsonl, anchor_map.json, coverage_report.json (~2.5 min)
uv run python -m vkrag.inspect_samples   # reports/stage1_samples.md
uv run vkrag gpuinfo           # data/external/gpuinfo/*.html -> gpuinfo_snapshot.json
uv run vkrag history           # vuid_history.json (~15 s, Headers json of 97 tags)
uv run vkrag strata [--freeze]  # strata.jsonl, samples.json (FROZEN 2026-11-07: a rerun must reproduce it), reports/strata_table.md
uv run vkrag cutoff-probe select|ask|judge|result   # data/processed/cutoff_probe/ (OpenRouter, ~$0.15)
uv run vkrag spirv             # data/raw/{SPIRV-Headers@fbf86836,GLSL} -> data/external/spirv_identifiers.txt
uv run vkrag questions prepare --sample pilot|main    # generation_log/batches/<sample>/batch_NNN.input.json + <sample>_assignments.json
uv run vkrag questions validate --sample pilot [--no-dedup]   # rejects, <sample>_validated.jsonl, <sample>_validation.json
uv run vkrag questions review --sample pilot   # reports/<sample>_questions.md + leak measures
uv run vkrag questions prepare --sample pilot --regen   # new batch for regenerate_vuids (same qids)
uv run vkrag questions freeze --sample pilot   # data/questions/pilot_questions.jsonl (immutable; main: questions.jsonl)
uv run vkrag index             # data/processed/index/: BM25 + bge-m3 dense/sparse (~4 min, Ollama unloaded)
uv run vkrag transform --run-id pilot   # phase A: qwen rewrite + HyDE -> runs/<id>/query_transforms.jsonl
uv run vkrag retrieve --run-id pilot [--configs all]   # phase B -> retrieved.jsonl + retrieval_metrics.json (~4 min)
uv run vkrag acceptable --run-id pilot [--dry-run] [--max-usd 1]   # stage 3b judge (OpenRouter, pilot $0.93) -> acceptable_vuids, final gold
uv run vkrag hypotheses        # runs/pilot/hypotheses.json (~45 s)
uv run vkrag report            # Stage 8: reports/{report_tables.md, report_data.json, figures/, error_candidates.md} (~15 s)
uv run --group report python notebooks/make_report_notebook.py   # executes notebooks/report.ipynb
```
Final report text: `reports/report.md` (hand-written; numbers from `report_tables.md`).
Question generation: one Claude Code subagent per batch (fresh context, own scratch dir), prompt `data/questions/generation_log/prompt_v2.md` (pilot used v1).
OpenRouter: `generation/openrouter.py` (key from `.env`, never print it); checks in `reports/openrouter_check.json`.
