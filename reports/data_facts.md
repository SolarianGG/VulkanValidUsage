# Data facts (PLAN §9.4), tag v1.4.366

Checked on 2026-11-07. Build: `khronosgroup/docker-images@sha256:f1ca671f…4762` (digest pinned in `BUILD.adoc` of the tag itself), `./makeSpec -spec all -O html validusage`, commit `a8b088a3`. Hashes: `data/build/build_info.json`.

## validusage.json
- `schema version: 2`. Layout: `validation → entity → condition → [{vuid, text, page}]`. 2,244 entities, **27,429 VUs** (20,575 explicit, 6,854 implicit).
- **Every VU has the condition `core`.** Extension conditions are resolved by the `-spec all` build and never reach the json. ⇒ Deviation from the plan: the VU condition (needed for strata) is reconstructed from the `ifdef::` stack in the adoc source (`ingest/adoc_conditions.py`); the json provides text only.
- The built json and `registry/validusage.json` from Vulkan-Headers v1.4.366 are **identical** (VUID sets and texts). The Headers copy is therefore reliable for historical tags (dating; §9.2 item 1, the 0.5% threshold is not exceeded).
- Explicit/implicit by suffix: explicit VUIDs have a numeric suffix. Text suffixes of implicit VUIDs (counts): parameter 3373, sType 1262, pNext 411, recording 267, cmdpool 267, videocoding 248, arraylength 189, parent 178, suspended 143, commonparent 141, unique 139, renderpass 119, zerobitmask 57, queuecount 42, bufferlevel 17, queuetype 1. No unknown suffixes. 669 implicit VUIDs have no parameter part (`VUID-X-commonparent`).
- 15 VUIDs keep a pre-promotion entity name (`VUID-VkBlitImageInfo2KHR-…` under the json key `VkBlitImageInfo2`); the entity is taken from the json key, the VUID name is stored as `vuid_entity`.
- HTML tags in the text: `a` (~145k), `code`, `strong class="purple"`, `span class="eq"` (497 VUs), `em`, `sub`/`sup`, block-level `div.ulist > ul > li > p` (nested lists inside VUs), `br`.
- Math in VU text is **raw TeX** `\(...\)` (20 VUs, e.g. `\left\lceil{\frac{a+b}{c}}\right\rceil`). Needs TeX → text normalization.
- HTML entities (`&#8217;`, `&lt;`) need `html.unescape`.
- Provisional extensions (5: `VK_AMDX_dense_geometry_format`, `VK_AMDX_shader_enqueue`, `VK_KHR_portability_subset`, `VK_NV_cuda_kernel_launch`, `VK_NV_displacement_micromap`) **are included** in `-spec all` and in the json. There are no VKSC rules.
- Entities outside vk.xml: `RuntimeSpirv` (363 VUs), `StandaloneSpirv` (201) → `entity_kind=spirv`; 125 SPIR-V built-ins (`Position`, `FragCoord`, `PrimitiveId`, …; 414 explicit VUs) → `entity_kind=builtin`.

## adoc source (for conditions)
- 8,295 VUID anchors `[[VUID-…]]` in chapters/appendices, 1,805 of them templated `[[VUID-{refpage}-…]]` (`commonvalidity`, expanded via `include::`).
- `ifdef` 8,376, `ifndef` 629. Under `-spec all` all extension attributes are defined ⇒ `ifndef::VK_*` content never reaches the build, so negation is not needed for VUs present in the json.
- Grammar: `,` is OR, `+` is AND, no parentheses, AND across levels comes from nesting. **One mixed expression**: `VK_COMPUTE_VERSION_1_4,VK_EXT_pipeline_protected_access+VK_EXT_graphics_pipeline_library` (`chapters/pipelines.adoc:5544`), read as `A , (B+C)` (`+` binds tighter; stock asciidoctor would read `B+C` as a single name); logged.
- Non-extension attributes used in ifdefs: `hidden`, `isrefpage`, `implementation-guide`, `editing-notes`, `site-gen-antora`; none are defined in the spec build.
- Tagged includes (`include::file.adoc[tag=…]`, including self-includes of a file) are used and must be honored.
- New version names: `VK_BASE_VERSION_x_y`, `VK_COMPUTE_VERSION_x_y`, `VK_GRAPHICS_VERSION_x_y` (`apitype="internal"` in vk.xml, sub-features of a version). For strata they collapse to version x.y (`conditions.version_of`, `simplify_versions`). An entity's core version may come from these feature blocks.
- Result of `adoc_conditions`: **all 20,575 explicit VUIDs** recovered, exact set match with the json, 0 unresolved includes/attributes, every VUID at exactly one site; 2 unbalanced `endif` lines (logged). Most frequent simplified conditions: `VK_VERSION_1_0` 1263, `core` 520, `VK_KHR_device_address_commands` 370, `VK_KHR_acceleration_structure` 306, `VK_EXT_descriptor_heap` 300, `VK_KHR_synchronization2,VK_VERSION_1_3` 248.
- `{generated}/` files contain no explicit VUID anchors (only `validity/`, i.e. implicit), so they are not walked.

## Single-page HTML (`vkspec.html`, 41.7 MB)
- Every VU appears exactly once: 27,429 `<a id="VUID-…">` anchors.
- Rule blocks: `div.sidebarblock > div.content > div.title` with text `Valid Usage` (1,198) or `Valid Usage (Implicit)` (2,087). Also `Host Synchronization` (381), `Command Properties` (279, a table), `Conditional Rendering` (267), `Structure Chaining` (833), `Return Codes` (310).
- The entity anchor sits on `div.listingblock id="vkCmdDraw"` (the C prototype) inside the refpage `div.openblock`; the intro sentence ("To record a non-indexed draw, call:") is in the same openblock before the listing. `Command Properties` and the VU blocks are inside that openblock as well.
- Math is KaTeX rendered **as HTML only** (`span.katex-html`, no MathML/TeX annotation): 1,104 occurrences, 172 `stemblock`s. KaTeX markup is linearized (`normalize.katex_to_text`).

## Ollama (Stage 0)
- `qwen3.5:9b` digest `56671c2ab938…`, Q4_K_M, 9.0B, **multimodal** (CLIP projector `qwen3vl_merger`, 922 MB blob, loaded together with the model).
- Modelfile defaults: `temperature 1`, `presence_penalty 1.5`, thinking **on** by default ⇒ every request sets `temperature=0`, `presence_penalty=0`, `think=false` explicitly.
- `think=false` is honored: the `thinking` field is empty and there is no `<think>` in content. Without it the model spends 256 tokens thinking and returns an empty answer (`done_reason=length`).
- `prompt_eval_count` on a repeated identical prompt is the full count (55), not only the new tokens, on this version (0.40.15). Usable as a sanity check; the local token count stays the criterion.
- ~~Blocker: Ollama did not see the GPU~~ (broken install, `cuda_v12/` without `ggml-cuda.dll`). **Fixed** by reinstalling on 2026-11-07: `library=CUDA`, RTX 3070 Laptop, driver 13.4, 7.0 GiB available.
- With the vision projector, `qwen3.5:9b` loads **12%/88% CPU/GPU** (32/33 layers; projector + 248 MB compute buffer). ⇒ A text-only variant **`qwen3.5-9b-text`** was created (`configs/ollama/qwen3.5-9b-text.Modelfile`): same weights blob `sha256:02d45dc1…`, same renderer/parser, no projector. Result: **100% GPU, 33/33 layers**, `ollama ps` 5.5 GB; 546 MB stay in CUDA_Host, which is the input token-embedding matrix (llama.cpp always keeps it on the CPU; this is not layer offload).
- Speed (`num_ctx=8192`, batch=1, warm): generation **59 tok/s**, prompt eval ~0.06 s for 32 tokens; repeats at `temperature=0` are deterministic.
- `keep_alive=0` really frees VRAM: 7.5 → 1.2 GB per `nvidia-smi`.
- VRAM: Windows/display take 1.2–1.9 GB; with qwen loaded 6.6 of 8 GB are used ⇒ ~1.5 GB free. bge-m3 fp16 (~1.1 GB) + reranker fp16 (~1.1 GB) + activations **do not fit** next to qwen ⇒ phase L will likely use the "sum of phases" scenario with a caveat (Stage 6); exact measurement after torch is installed.
- HTTP client: use `127.0.0.1`, not `localhost` (on Windows a request loses ~2 s on the IPv6 attempt).

## Stage 1 results (corpus `5e83355c…`, `data/processed/coverage_report.json`)
- Sections from HTML: 3,101 refpage blocks + 4,695 prose units (sect1..sect5); 3,285 VU blocks removed, all inside refpage openblocks; all 27,429 VUIDs mapped to a parent section.
- Chunks: 4,027 refpage parts + 5,301 prose parts + 27,429 VU chunks; 637 sections split into several parts. Section parts are at most 797 tokens (max over qwen / XLM-R / DeepSeek V4 Flash tokenizers; XLM-R is the binding one, ~2× qwen on identifiers).
- Token lengths (max of three), p50 / p90 / p99 / max: prose 129 / 677 / 778 / 797; refpage 400 / 757 / 792 / 797; VU 98 / 203 / 279 / 5518.
- VU chunks over 800 tokens: 0 explicit, 2 implicit (`VUID-VkDeviceCreateInfo-pNext-pNext`, `VUID-VkPhysicalDeviceProperties2-pNext-pNext`: lists of every allowed pNext structure; also over 1024 XLM-R tokens, so they are truncated by the embedder/reranker). Implicit VUs are not used for questions.
- The VU header uses a compact availability tag (distinct extensions/versions, at most 3 + "(+N more)"); the full DNF stays in `condition`.
- **Coverage: 100%** of explicit VUIDs have a VU chunk and a parent section (threshold 99%). Built json vs Headers: no differences. `refs` anchors: 6,031 distinct, 2 unresolved (`legacy-dynamicrendering`, `builtin-volatile-semantics`). Headings without own text resolve to the first unit inside the section.
- Chunk ids and the corpus hash are deterministic (two consecutive rebuilds give the same hash).
- Equivalence classes (explicit), **decided 2026-11-07: raw identical text only** (`corpus.equiv_text_placeholder: false`): 7,261 classes, 845 text merges on top of the numeric-suffix rule (all api), largest 40 VUs (`commonvalidity` over draw/dispatch/trace-rays commands). The rejected placeholder variant gave 6,942 classes and merged distinct rules of different SPIR-V built-ins into 87-/48-VU classes. The corpus hash covers chunk texts only, so it does not change with the class rule; classes live in `vuids.jsonl`.
- Manual review sample: `reports/stage1_samples.md` (10 random chunks per type, 10 largest classes).

## Stage 2 inputs (2026-11-07)

### gpuinfo.org snapshot (`data/external/gpuinfo_snapshot.json`, `vkrag gpuinfo`)
- Source: pages `listextensions.php?platform=windows|linux` saved manually by the user on 2026-11-07
  (`data/external/gpuinfo/*.html`). Filters on the saved pages: age **"Recent (1y)"**, all Vulkan versions.
  The plan asked for a 24-month window; the site offers only "Recent (1y)" or "Historic (All)".
- Metric: "Device coverage" = share of devices reporting the extension. Windows: 410 extensions, Linux: 367.
- **The page lists device extensions only.** 43 instance extensions of the registry (`VK_KHR_surface`,
  `VK_KHR_win32_surface`, `VK_EXT_debug_utils`, `VK_KHR_get_physical_device_properties2`, ...) are absent, so
  they currently fall into `ext_niche`. 231 eligible explicit VUs have an instance extension on their deciding
  path (212 of them `VK_KHR_surface`). Needs the instance-extension pages (`listinstanceextensions.php`).
- 22 names on the pages are not in the v1.4.366 registry (KHX, internal/driver-private, e.g. `VK_NV_internal_handle`); ignored.
- **Instance pages added** (`listinstanceextensions.php`, Recent 1y): Windows 27, Linux 30 extensions;
  `VK_KHR_surface` 1.00, `VK_KHR_win32_surface` 1.00 (Windows), `VK_KHR_wayland_surface` / `xcb` 0.99 (Linux),
  `VK_EXT_debug_utils` 1.00, `VK_KHR_display` 0.74. 48 registry extensions remain absent (vendor / non-desktop).
  With instance pages: KHR/EXT >= 50%: min 164, mean 186, platform 195, max 216. ext_niche 12,492, ext_popular 2,756.
- Combine rule `platform` (approved 2026-11-07): mean over Windows and Linux; extensions bound to a window system (vk.xml
  `platform` = win32 / xlib / xcb / wayland) are rated on their own OS only. KHR/EXT extensions >= 50%:
  min 151, mean 167, platform 172, max 190. Borderline examples: `VK_EXT_mesh_shader` 0.487,
  `VK_KHR_ray_tracing_pipeline` 0.503.

### VU dating (`data/processed/vuid_history.json`, `vkrag history`)
- Window: tags released from 2023-11-07 (3 years before the freeze) up to v1.4.366, plus baseline `v1.3.269`;
  97 tags scanned, `v1.4.308` skipped (no `registry/validusage.json` in Headers at that tag). ~15 s.
- Explicit VUs: 13,850 already present in the baseline (`before_window`), **6,725 first appeared inside the window**, 0 undated.
- Suffix-monotonicity proxy (sanity check only): Spearman(suffix, first tag) = 0.84; 188 VUs dated inside the
  window have a suffix below the maximum suffix of the baseline (numbers are allocated before publication).
- `text_changed_recently` vs `v1.4.356` (10 tags back): 778 VUs (590 by Levenshtein > 0.1, 188 by a changed
  identifier set only, e.g. a new `imageLayout` or `pInputAssembly` -> `pInputAssemblyState`); 143 VUs are new in
  the last 10 tags. Old text is matched by VUID (20,366), suffix + canonical entity (52) or closest text with the
  same suffix (14).

### Strata, provisional (`vkrag strata --allow-no-recent`, `reports/strata_table.md`)
- Eligible explicit VUs: 19,472; excluded: 582 `specialuse_entity`, 521 `provisional_condition`
  (0 obsoleted entities, 0 unknown condition names).
- Base strata of eligible VUs: ext_niche 12,640 (764 entities), ext_popular 2,608 (273), core_promoted 2,429 (255),
  core_1_0 1,795 (201). `recent` needs the cutoff dates.
- Largest ext_niche drivers: `VK_KHR_device_address_commands` (new, low coverage; in `commonvalidity` templates),
  `VK_EXT_mesh_shader` (0.487, just below the threshold), `VK_EXT_descriptor_heap`, `VK_NV_mesh_shader`.
- 963 eligible VUs belong to entities outside vk.xml (SPIR-V, built-ins); their origin is taken as core 1.0, so
  their stratum is decided by the adoc condition alone.

### OpenRouter (`reports/openrouter_check.json`, PLAN §9.4)
- Key limit is **$100** (not $10 as in §9.1), $0.52 already spent before this project's checks; no reset interval.
- `deepseek/deepseek-v4-flash-0731` (canonical `deepseek-v4-flash-20260731`, HF `deepseek-ai/DeepSeek-V4-Flash-0731`):
  29 endpoints; bf16/fp8 with temperature: DeepInfra fp8 ($0.06/$0.18 per M), Baidu fp8, CoreWeave, Cohere, Nebius,
  Parasail, Morph bf16 ($0.142/$0.40), and others. With `reasoning: {enabled: false}` every tested provider returned
  0 reasoning tokens. Routing with `allow_fallbacks: false`, `require_parameters: true`, `data_collection: deny`,
  `quantizations: [bf16, fp8]` and a pinned `provider.order` works; the response carries `model`, `provider` and
  `usage.cost`; `/generation` confirms the provider. Repeats at temperature 0 were identical on DeepInfra, Cohere, Baidu,
  different on Nebius, Parasail, CoreWeave, Morph. Providers disagree on content (Morph bf16 answered "Yes" to the
  render-pass question, all fp8 endpoints "No").
- `google/gemini-3.8-flash`: endpoints Google AI Studio (standard, flex at 50% price, priority) and Vertex (no
  `temperature`). `response_format` json_schema (strict) works on AI Studio standard and flex; reasoning effort medium
  used 171-205 reasoning tokens on a short grading prompt, ~$0.0011 per call (flex ~$0.0006). The response reports
  the provider as "Google AI Studio" for both tiers. Neither model has `knowledge_cutoff` in `/models`.

### Cutoff probe, first run (`data/processed/cutoff_probe/`, PLAN §9.1 method as written)
- 88 extensions first published 2024-05…2026-10 (≤ 5 per month; 2 months have none). Answerers: qwen3.5-9b-text
  (Ollama, ~1.3 s/answer) and DeepSeek V4 Flash (DeepInfra fp8, total $0.001). Judge: Gemini 3.8 Flash (AI Studio),
  176 calls, $0.13.
- qwen recognized **1 of 88** (2024-11); it often claims the extension does not exist. DeepSeek recognized 10 of 88,
  scattered (2024-08 … 2026-06), no month above 50% after 2024-09.
- The rule "last month ≥ 50% followed by two months < 50%" gives no cutoff for qwen and 2025-03 for DeepSeek (based on
  1/2 recognized); with 1-5 items per month the rule is dominated by noise. The window does not reach back to months
  the models know, so there is no baseline recognition level.

### Cutoff probe, variant (a) (approved 2026-11-07)
- All 177 extensions with a Description section first published 2022-01…2026-10 (baseline tag v1.2.203), quarterly bins.
  Cost: answerer $0.002, judge $0.29 for 354 calls. DeepInfra returned 429 (shared upstream pool) once; the client
  now retries 3 times with backoff.
- DeepSeek V4 Flash: 43/177 recognized. 2022-Q2…2024-Q1 at 29-58% per quarter (2022-Q3 7/12, 2024-Q1 4/7);
  from 2024-Q4 on 0-29% (2025: 7/49). Rule -> **cutoff 2024-Q3 (2024-09-30)**, based on 3/6 in that quarter.
  The pre-cutoff recognition level itself is only ~45%, so the 50% threshold is near the noise level.
- qwen3.5-9b-text: 5/177 recognized at every age (2022 included); it usually denies that the extension exists.
  The probe cannot date qwen's cutoff: the model does not know Vulkan extensions at all.
- Recent stratum size (eligible explicit VUs dated after the cutoff): 2024-06-30 5,554 / 2024-09-30 5,184 /
  2024-12-31 5,000 / 2025-03-31 4,710 (mostly ext_niche; ~460 entities, ~1,800 classes at 2024-09-30).

### Final strata and frozen sample (2026-11-07, `recent_cutoff` 2024-09-30 for both answerers)
- Eligible 19,472: recent 5,184 (459 entities, weight 0.266), ext_niche 7,907 (0.406), ext_popular 2,484 (0.128),
  core_promoted 2,264 (0.116), core_1_0 1,633 (0.084).
- Main 400 = 5 × 80, 244 entities (≤ 3 each), one VU per equivalence class; pilot 45 = 5 × 9, disjoint from main
  by VUID and class. Entity kind in main: 379 api, 15 builtin, 6 spirv. 7 main VUs have `text_changed_recently`.
- Base strata of the 80 `recent` VUs: ext_niche 73, core_promoted 4, ext_popular 2, core_1_0 1 (recency is confounded
  with extension niche-ness; report limitation).
- Sensitivity of the main sample: cutoff 2024-06-30 would move 12 VUs into recent; 2024-12-31 moves 1 out; 2025-03-31 moves 8 out.
- `samples.json` sha256 `e63d2b5e2eafdb03365a9eb6e446c206b2440613855eb4d968f1497a249ed7be`; resampling is deterministic.
