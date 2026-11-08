"""CLI: vkrag <command>."""
from __future__ import annotations

import typer

app = typer.Typer(no_args_is_help=True, add_completion=False)
spec_app = typer.Typer(no_args_is_help=True)
app.add_typer(spec_app, name="spec")


@spec_app.command("select-tag")
def spec_select_tag(write: bool = typer.Option(True, help="Write the tag into the config")) -> None:
    """Select the v1.4.NNN tag using the rule from PLAN §9.1."""
    from vkrag.ingest.spec_build import select_tag

    select_tag(write=write)


@spec_app.command("build")
def spec_build() -> None:
    """Docker build of the single-page HTML and validusage.json, copied into data/build."""
    from vkrag.ingest.spec_build import build

    build()


@app.command()
def registry(history: bool = typer.Option(True, help="Build identifiers.json over all tags")) -> None:
    """vk.xml → aliases.json, registry.json, identifiers.json."""
    from vkrag.ingest.registry import run

    run(history=history)


@app.command()
def ingest(history: bool = typer.Option(True, help="Also rebuild identifiers.json over all tags")) -> None:
    """vk.xml registry, adoc VU conditions and normalized VU records (vu_base.jsonl)."""
    import json

    from vkrag.ingest import adoc_conditions, registry, vu

    registry.run(history=history)
    rep = adoc_conditions.run()
    print("adoc conditions:", json.dumps({k: rep[k] for k in ("vuids", "multi_site_vuids", "stats", "unresolved_count", "mixed_expressions")}))
    print("vu records:", json.dumps(vu.run()))


@app.command()
def chunk() -> None:
    """Sections, VU chunks, equivalence classes, length limits and coverage report."""
    import json

    from vkrag.chunking import run

    cov = run()
    keys = ("explicit_total", "coverage", "chunks_by_type", "sections_split", "length_tokens_max_of_three", "vu_chunks_over_limit", "refs_unresolved")
    print(json.dumps({k: cov[k] for k in keys}, indent=1, default=dict))
    eq = cov["equivalence"]
    print("equivalence:", json.dumps({k: eq[k] for k in ("explicit_classes", "merged_by_text_only", "merged_by_text_by_entity_kind")}), "largest:", [(x["size"], x["class"]) for x in eq["largest"][:5]])
    threshold = 0.99
    if cov["coverage"] < threshold:
        raise typer.Exit(f"coverage {cov['coverage']:.4f} below {threshold}")


@app.command()
def gpuinfo() -> None:
    """Saved gpuinfo.org extension pages -> data/external/gpuinfo_snapshot.json."""
    import json

    from vkrag.config import load_config
    from vkrag.ingest import gpuinfo as g

    s = g.run()
    print(json.dumps({k: s[k] for k in ("date", "platforms", "window", "combine", "unknown_to_registry", "registry_missing_from_snapshot")}))
    thr = load_config()["strata"]["popularity_threshold"]
    print(f"KHR/EXT extensions >= {thr} by combine rule:", g.sensitivity(thr))


@app.command()
def history() -> None:
    """vuid_history.json: first tag of each numeric VUID suffix, text_changed_recently."""
    import json

    from vkrag.history import run

    h = run()
    print(json.dumps({k: h[k] for k in ("window_start", "baseline_tag", "text_change_old_tag", "tags_scanned", "tags_skipped", "stats", "monotonic_check")}, indent=1))


@app.command()
def strata(allow_no_recent: bool = typer.Option(False, help="Sample a provisional preview while the recent cutoff is unknown"),
           freeze: bool = typer.Option(False, help="Freeze samples.json after sampling")) -> None:
    """Strata, exclusions, main/pilot samples and reports/strata_table.md."""
    import json

    from vkrag import strata as st

    print(json.dumps(st.run(allow_no_recent=allow_no_recent), indent=1))
    if freeze:
        s = st.freeze()
        print("frozen", s["frozen_at"], s["sha256"])


@app.command()
def spirv() -> None:
    """SPIRV-Headers grammars + GLSL sources -> data/external/spirv_identifiers.txt."""
    import json

    from vkrag.ingest.spirv_ids import build

    print(json.dumps(build(), indent=1))


questions_app = typer.Typer(no_args_is_help=True)
app.add_typer(questions_app, name="questions")


@questions_app.command("prepare")
def questions_prepare(sample: str = typer.Option("pilot", help="main | pilot"),
                      regen: bool = typer.Option(False, help="Only new batches for `regenerate_vuids` of the last validation")) -> None:
    """Generator batches for Claude Code (PLAN §9.3, Stage 3a)."""
    import json

    from vkrag.questions.prepare import prepare, prepare_regen

    print(json.dumps(prepare_regen(sample) if regen else prepare(sample), indent=1))


@questions_app.command("validate")
def questions_validate(sample: str = typer.Option("pilot", help="main | pilot"),
                       dedup: bool = typer.Option(True, help="bge-m3 cosine near-duplicate check (GPU)")) -> None:
    """Automatic checks of batch outputs; rejects go to batch_NNN.rejects.jsonl."""
    import json

    from vkrag.questions.validate import validate

    r = validate(sample, dedup=dedup)
    print(json.dumps({k: r[k] for k in ("missing_outputs", "accepted_lines", "reject_reasons", "regenerate_vuids", "superseded", "unanswerable")}, indent=1))
    if r["near_duplicates"]:
        print("near duplicates:", json.dumps(r["near_duplicates"]["pairs"]))


@questions_app.command("freeze")
def questions_freeze(sample: str = typer.Option("pilot", help="main | pilot"),
                     force: bool = typer.Option(False, help="Overwrite an existing set (only before approval)")) -> None:
    """Immutable question set with question_hash and graded gold_chunk_ids (Stage 3a)."""
    import json

    from vkrag.questions.freeze import freeze

    print(json.dumps(freeze(sample, force=force), indent=1))


@questions_app.command("review")
def questions_review(sample: str = typer.Option("pilot", help="main | pilot")) -> None:
    """reports/<sample>_questions.md for manual review + n-gram strictness comparison."""
    import json

    from vkrag.questions.review import review

    print(json.dumps(review(sample), indent=1))


@app.command()
def index(which: str = typer.Option("all", help="all | bm25 | dense (dense also builds sparse)")) -> None:
    """Stage 4: BM25, dense (FAISS) and sparse indexes in data/processed/index/."""
    import json

    from vkrag.index.build import build

    print(json.dumps(build(which), indent=1))


@app.command()
def transform(sample: str = typer.Option("pilot", help="main | pilot"),
              run_id: str = typer.Option("pilot", help="runs/<run_id>/")) -> None:
    """Phase A: query rewrite and HyDE by the local qwen -> runs/<run_id>/query_transforms.jsonl."""
    import json

    from vkrag.retrieval.transform import run

    print(json.dumps(run(sample, run_id), indent=1))


@app.command()
def retrieve(sample: str = typer.Option("pilot", help="main | pilot"),
             run_id: str = typer.Option("pilot", help="runs/<run_id>/"),
             configs: str = typer.Option("", help="Comma-separated configurations; default: base ones, `all`: base + transform ones")) -> None:
    """Phase B: retrieval for all questions -> runs/<run_id>/retrieved.jsonl, then retrieval metrics."""
    import json

    from vkrag.eval.retrieval_metrics import evaluate, table
    from vkrag.retrieval.run import BASE_CONFIGS, TRANSFORM_CONFIGS, run

    cs = tuple(c for c in configs.split(",") if c) or BASE_CONFIGS
    if cs == ("all",):
        cs = BASE_CONFIGS + TRANSFORM_CONFIGS
    print(json.dumps(run(sample, run_id, cs), indent=1))
    print(table(evaluate(sample, run_id)))


@app.command()
def acceptable(sample: str = typer.Option("pilot", help="main | pilot"),
               run_id: str = typer.Option("pilot", help="runs/<run_id>/ with the rrf_rerank ranking"),
               dry_run: bool = typer.Option(False, help="Only count calls and estimate the cost"),
               max_usd: float = typer.Option(1.0, help="Stop when the estimate or the spend exceeds this"),
               apply_only: bool = typer.Option(False, "--apply", help="Only write the cached verdicts into the question file"),
               limit: int = typer.Option(0, help="Judge only the first N pending pairs (usage probe)")) -> None:
    """Stage 3b: judge the top-10 out-of-class VU chunks -> acceptable_vuids, final gold."""
    import json

    from vkrag.questions import acceptable as acc

    if not apply_only:
        print(json.dumps(acc.run(sample, run_id, dry_run=dry_run, max_usd=max_usd, limit=limit or None), indent=1))
    if not dry_run and not limit:
        print(json.dumps(acc.apply(sample, run_id), indent=1))


@app.command("cutoff-probe")
def cutoff_probe(step: str = typer.Argument(..., help="select | ask | judge | result"),
                 models: str = typer.Option("qwen,remote", help="Answerers for `ask`")) -> None:
    """recent_cutoff_date probe by extensions (PLAN §9.1)."""
    import json

    from vkrag import cutoff_probe as cp

    if step == "select":
        r = cp.select()
        print(json.dumps(r["per_month"]), "items:", len(r["items"]))
    elif step == "ask":
        cp.ask(models.split(","))
    elif step == "judge":
        cp.judge()
    elif step == "result":
        print(json.dumps(cp.result(), indent=1))
    else:
        raise typer.BadParameter(step)


if __name__ == "__main__":
    app()
