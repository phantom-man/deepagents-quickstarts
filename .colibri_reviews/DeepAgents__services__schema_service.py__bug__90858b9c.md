# Colibri review — DeepAgents/services/schema_service.py (bug)

- source: `C:\Users\User\source\repos\deepagents-quickstarts\DeepAgents\services\schema_service.py`
- model: claude-fable-5-1 (in-session Phase-3 gate over the external raw `z-ai/glm-5.3-flash` review, `.colibri_reviews/_external_raw/da__schema_service.py__z-ai-glm-5.3-flash.md`)
- sha256: `90858b9c552e1762731d6485c2dcb6f1a1e98bd30801cb7ef5899c8be7f2a6e7` (current bytes at dispatch, 2026-09-05; identical to the bytes the external reviewer saw)
- date: 2026-09-05
- mode: bug
- context pack: jCodemunch symbol map + call-site search on `deepagents-quickstarts`; the external raw review; no prior `.colibri_reviews` record for this file; no remediation manifest exists in this repo. Every external finding was re-traced against the cited lines (Phase 3): CONFIRMED / PLAUSIBLE kept, refuted ones listed with the reason so they are never re-fixed (G35).

## Verdict
One confirmed HIGH that misrenders the file's own first-party schemas; the rest is polish.

## Bugs & vulnerabilities
**[HIGH] File-keyword heuristic runs before the type checks — CONFIRMED** - `line 1057-1083 vs 1086-1094, 814-823`
- `FILE_KEYWORDS` contains `audio` and `image`, and the heuristic precedes the boolean/number branches, so the schemas defined in this same file misrender: `veo-3.1-generate-001.generate_audio` (boolean, 341-345) → `AUDIO_FILE` picker plus a bogus `AssetRequirement(asset_type="audio")` (1197-1236); `imagen-3.0-generate-002.number_of_images` (integer 1-4, 495-499) → `IMAGE_FILE` upload instead of a slider.
- Fix: gate the file heuristic on `prop_type == "string"` (or `format == "uri"`), and match keywords on token boundaries.

**[LOW] `output_type` inferred only for array outputs — CONFIRMED (downgraded from MEDIUM)** - `line 1242-1260`
- Every string/uri model reads "unknown". jCodemunch found no consumer of `ModelSchema.output_type` beyond serialisation (934, 979; `model_registry` has its own enum), so the wrong value is currently inert.

**[LOW] Shallow copies alias class-level schema constants — PLAUSIBLE** - `line 557, 759, 1173`
- `raw_schema` and `control.options` share objects with `VERTEX_SCHEMAS`/`GENAI_SCHEMAS`; no mutating consumer traced.

**[LOW] `get_schema` raises on a cache-write failure after success — CONFIRMED** - `line 1316-1318`

**[LOW] Duration regex matches any s-word — CONFIRMED** - `line 1224`
- `(?:second|sec|s)`; gated by the 1220 pre-check so a false hit needs "duration"/"second" elsewhere in the text.

**[LOW] Unguarded singleton — CONFIRMED** - `line 1377-1382`

**[LOW] "Applied quality default overrides" logged even when nothing matched — CONFIRMED** - `line 192-195, 213-215`

## Fixed since this review
- **HIGH file-keyword heuristic before the type checks — FIXED 2026-09-06** (the commit carrying
  this note): the file branch in `_infer_control_type` is now gated on `prop_type in ("string", "array")`
  (untyped properties default to string, so `input_file` with only a description still renders
  as FILE; arrays keep their file treatment so Replicate list-of-uri params such as `images` do
  not regress to TEXT - pinned by a test that passed before the fix too); booleans and numbers fall through to their own branches. The record's second
  suggestion (token-boundary keyword matching) was NOT taken — the type gate alone closes both
  recorded misrenders and every real file parameter in the first-party schemas is string-typed;
  boundary matching would change the rendering of other params and is a separate change.
  TDD: `tests/test_schema_service_control_inference.py` — Veo `generate_audio` (boolean) is a
  CHECKBOX with no AssetRequirement, Imagen `number_of_images` (integer 1-4) is a SLIDER, both
  through `_parse_openapi_schema` over the Vertex provider's own schemas; four string file
  params still render as IMAGE/AUDIO/VIDEO/FILE. RED on the old bytes (AUDIO_FILE / IMAGE_FILE),
  GREEN now (9 tests).
- The LOWs (output_type inference, aliasing copies, cache-write raise, duration regex,
  singleton, misleading log) stay open.
