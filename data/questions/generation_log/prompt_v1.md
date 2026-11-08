# Question generator prompt, version 1

You are generating evaluation questions for an experiment that measures how well language models
answer questions about Vulkan **Valid Usage (VU)** rules, with and without retrieval over the
specification. You process exactly one batch file and write exactly one output file. Work only
from the text given in the batch: never add facts from your own knowledge to a reference answer.

## Input

`batch_NNN.input.json`:
- `items[]`: one target VU each: `vuid`, `entity`, `entity_kind` (`api` | `spirv` | `builtin`),
  `stratum`, `vu_text` (the target rule), `vu_chunk` (the rule with its availability header),
  `answer_type` (assigned by code), `expected_verdict` (only for `yes_no`), `qids`
  (`{"identifier": ..., "descriptive": ...}`), `related_entities`, `ref_chunks` (ids of sections the
  rule links to).
- `context.entities{name}`: `section_parts` (the entity's definition and prose, without VU blocks)
  and `vus[]`: **every** explicit and implicit VU of that entity. A VU whose text is identical to an
  earlier one in the batch carries `same_text_as: <vuid>` instead of `text`.
- `context.ref_chunks{chunk_id}`: sections linked from the rules.

## Output

Write `batch_NNN.output.jsonl` next to the input: **two lines per item** (one per style, in the
order `identifier`, `descriptive`), UTF-8, one JSON object per line, no other text:

```json
{"qid": "...", "vuid": "...", "style": "identifier|descriptive", "answer_type": "rule|yes_no|scenario",
 "question": "...", "reference_answer": "...", "expected_verdict": "yes|no",
 "descriptive_infeasible": false, "downgraded_to_rule": false, "verdict_changed": false,
 "checked_entities": ["..."], "checked_vuids": ["..."], "also_relevant_vuids": [], "notes": "..."}
```

- `qid`: copy from `items[].qids[style]`. `vuid`: the target VU.
- `answer_type`: the assigned type, or `rule` if you downgraded (then `downgraded_to_rule: true` and
  say why in `notes`). Both styles of one item must have the same final `answer_type`.
- `expected_verdict`: only for `yes_no`; the verdict the reference answer gives. If the assigned
  verdict cannot be built honestly, flip it and set `verdict_changed: true` (both styles alike).
- `checked_entities`: entities all of whose VUs you checked the question against (at least the
  target entity and, for `scenario`, every entity in `related_entities`). `checked_vuids`: any other
  individual VUs you checked. The validator requires every VU of the target entity to be covered.
- `also_relevant_vuids`: other VUs (outside the target's text) that the reference answer also
  depends on or that a careful reader could cite as an equally good answer. It should be empty;
  if it is not, reformulate. Leave a non-empty list only when you cannot avoid it.
- `descriptive_infeasible`: `true` only if the rule cannot be asked about at all without naming
  API identifiers. Then the `descriptive` line has `"question": null`, `"reference_answer": null`.
- `notes`: optional, short.

## Rules for every question

1. **One rule, one answer.** The question must have a single unambiguous answer that follows from
   the target VU alone (or from VUs with the same text). Before writing, check the question against
   **all** VUs of the target entity and its related entities: no other VU may change, extend or
   contradict the answer. Conditions in the rule ("if ... was created with ...") must be stated in
   the question so that the rule clearly applies.
2. **No quoting.** Paraphrase. Do not copy any run of more than 5 consecutive ordinary words from
   the VU text (identifiers do not count, but connecting words between them do). Restructure the
   sentence rather than substituting synonyms word by word.
3. **No VUIDs**, no numbers of VUs, no "according to the Valid Usage" or "the spec says".
4. **Natural user voice**: a developer asking about their code or design ("I'm recording...",
   "Is it valid to...", "What must hold for..."). One or two sentences, at most ~60 words.
5. The question must not reveal the answer (no "must X be true, since it must?").
6. **Reference answer**: 1–3 sentences, complete and self-contained, states the requirement and
   the conditions under which it applies, derived only from the given text. It may (and for
   `identifier` style should) use exact identifiers. For `yes_no`, start with "Yes." or "No.".

## Styles

- `identifier`: name the API entities, parameters, enums, flags, features, SPIR-V decorations or
  built-ins exactly as in the spec (`vkCmdCopyImage`, `srcImageLayout`, `VK_IMAGE_LAYOUT_GENERAL`).
- `descriptive`: **no identifiers at all**: no `vk`/`Vk`/`VK_` names, no camelCase or SNAKE_CASE
  tokens, no SPIR-V / GLSL names (`FragDepth`, `OpImageWrite`, `Uniform` storage class, `gl_Position`),
  no extension names. Describe the situation in ordinary words ("when copying between two images",
  "the layout the destination image is in", "a fragment shader output that writes depth").
  Single plain words that are also member names (buffer, image, size, offset, flags, format,
  layout, stage) are fine in lower case. The question must still pin down the same rule; the
  reference answer may use identifiers.

The two styles of one item are paraphrases of the same question: same rule, same conditions,
same answer type, same verdict.

## Answer types

- `rule`: ask what is required / allowed / forbidden in the situation. Reference = the requirement.
- `yes_no`: only "Is it required / Is it allowed / Must ... / Can ... when Y?" about a single
  requirement; never "is this whole scenario valid?". The answer to the question must be
  `expected_verdict`. A "no" question typically asks whether something the rule forbids is allowed,
  or whether something is required that the rule does not require **only if** the given text
  clearly shows it is not required (otherwise flip the verdict). Do not use double negations.
- `scenario`: a short concrete situation (what the application does, with the relevant settings)
  that violates **exactly the target rule** and nothing else; the question asks what is wrong or
  whether it is valid. Check the scenario against every VU of the target entity and every related
  entity (list them in `checked_entities`). Fill in every value that another VU constrains so that
  no second violation exists. If you cannot guarantee a single violation, downgrade to `rule`.
  Reference = which requirement is violated and why.

## Unanswerable batch (`batch_unans.input.json`)

Write `batch_unans.output.jsonl`, one line per question, `qid` = `qid_prefix` + two-digit number
starting from `01`, `stratum: "unanswerable"`, both styles are not required (`style: "identifier"`):

```json
{"qid": "...", "subtype": "nonexistent|false_rule|false_behavior", "style": "identifier",
 "question": "...", "reference_answer": "...", "rationale": "...", "spec_evidence": [{"source": "VUID-... | section title", "text": "..."}],
 "invented_identifiers": ["..."], "notes": "..."}
```

- `nonexistent` (quota `quotas.nonexistent`): ask about a plausible but non-existent command,
  structure, enum value, flag, feature or extension. List the invented names in
  `invented_identifiers`; each must be absent from every source in `identifier_sources` (search
  those files). Reference: "There is no such ... in Vulkan." plus what exists instead, if obvious.
- `false_rule`: ask about a requirement that does not exist (presupposing it), for one of the
  `candidate_entities`. `spec_evidence` must quote the text (VU or section) from which it follows
  that the rule does not exist or that the opposite holds. Reference: the premise is false + what
  the spec actually requires.
- `false_behavior`: a false premise about how an existing entity behaves (its purpose, a
  parameter's meaning, an effect), refuted by its `section_parts`; quote them in `spec_evidence`.
- The question must sound as natural and confident as an answerable one; the false premise must be
  refutable from the quoted text, not from your memory.

## Final check before writing

For every line: valid JSON, the `qid` copied exactly, no VU text run > 5 words, no identifiers in
`descriptive`, `checked_entities` include the target entity, `answer_type` and `expected_verdict`
consistent across the two styles.
