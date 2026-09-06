=== hy4_review | z-ai/glm-5.3-flash | sha256 90858b9c552e1762 | C:\Users\User\source\repos\deepagents-quickstarts\DeepAgents\services\schema_service.py
=== 171s | in=10687 out=7703
==================================================================
# Review: `services/schema_service.py`

## HIGH — `_infer_control_type`: file-keyword heuristic runs before type checks, misclassifying non-string params as file uploads

**Location:** `_infer_control_type`, the `if is_file_param or is_uri_format:` block (before the `prop_type == "boolean"` / `prop_type in ("integer", "number")` checks).

**Trigger:** Any non-string parameter whose name contains a `FILE_KEYWORDS` substring. Concrete instances in this repo's own hardcoded schemas:
- `veo-3.1-generate-001` → `generate_audio` (boolean): `"audio" in name_lower` → classified `AUDIO_FILE`.
- `imagen-3.0-generate-002` → `number_of_images` (integer): `"image" in name_lower` → classified `IMAGE_FILE`.

**Impact:** For Veo 3.1, a boolean audio toggle is rendered as an audio file picker, and `_parse_openapi_schema` emits a bogus `AssetRequirement(asset_type="audio")` for it. For Imagen 3, the image-count slider (1–4) becomes an image upload control. The zero-touch UI is wrong for first-party models defined in this same file. The same substring matching (`"reference"` ⊂ "preferences", `"input_"`, `"file" in description`) will misfire on any future schema.

**Fix:** Only apply the file heuristic when the property is actually a file-ish string: gate it on `prop_type == "string"` (or `prop_format == "uri"` / `anyOf` with uri), i.e. move the boolean/integer/number checks above the file check, and match `FILE_KEYWORDS` on token boundaries (e.g. `name_lower.startswith(kw) or f"_{kw}" in name_lower`) instead of raw substring.

## MEDIUM — `output_type` is only inferred for array outputs; all single-URI outputs stay `"unknown"`

**Location:** `_parse_openapi_schema`, the `if "items" in output_schema:` block.

**Trigger:** Any model whose Output schema is `{"type": "string", "format": "uri"}` — which is every Veo, Lyria, MusicFX, and TTS schema in this file (only `imagen-3.0-generate-002` uses an array).

**Impact:** `ModelSchema.output_type` is `"unknown"` for all video/audio models handled by the Vertex/GenAI providers. Any consumer branching on `output_type` (downstream asset handling, GUI display) silently gets the wrong value. The model-name keyword inference exists but is dead code for the majority of models because it's nested inside the `items` branch.

**Fix:** Infer from `output_schema.get("items", {}).get("format")` when `type == "array"`, and from `output_schema.get("format")` when `type == "string"`; run the model-name keyword fallback in both cases.

## MEDIUM — Shallow `copy()` of class-level schema constants leaks shared mutable state

**Location:** `VertexAISchemaProvider.fetch_schema` (`schema_data = self.VERTEX_SCHEMAS[model_name].copy()`) and `GoogleGenAISchemaProvider.fetch_schema` (same pattern).

**Trigger:** Any caller mutating the returned schema graph — e.g. `schema.raw_schema` (which is the *same dict object* as `VERTEX_SCHEMAS[...]["openapi_schema"]`), or `ControlDefinition.options` (which is assigned the *same list object* as `prop["enum"]` in `_parse_openapi_schema`).

**Impact:** The `.copy()` is shallow, so the nested `openapi_schema`/`properties`/`enum` objects are shared with the process-lifetime class constants. One mutation (GUI code appending to `options`, an agent tweaking `raw_schema`, a future override pass like `_apply_default_overrides`) permanently corrupts the static schema for every subsequent call and every cached copy, with no error.

**Fix:** Use `copy.deepcopy(self.VERTEX_SCHEMAS[model_name])` (same for `GENAI_SCHEMAS`), and in `_parse_openapi_schema` use `control.options = list(prop["enum"])`.

## LOW — `get_schema` raises on cache-write failure after a successful fetch

**Location:** `get_schema`, the `with open(cache_path, "w", encoding="utf-8") ... json.dump(...)` block.

**Trigger:** Disk full, read-only cache directory, or (on Windows) a concurrent `open(..., "w")` on the same cache path from another thread/instance.

**Impact:** The schema was successfully fetched and parsed (and already placed in `_schema_cache`), but the caller receives an `OSError`/`JSONEncodeError` instead. The docstring contract says `ValueError` on fetch failure only; a non-critical cache write fails the whole request, and the next call inconsistently succeeds via the memory cache.

**Fix:** Wrap the disk write in `try/except OSError` and log a warning; the memory cache already covers the process lifetime.

## LOW — Duration regex has no word boundary; `"s"` alternative matches any s-word after a number

**Location:** `_parse_openapi_schema`, `re.search(r"(\d+)\s*(?:second|sec|s)", desc_lower)`.

**Trigger:** An asset-parameter description containing a number followed by whitespace and any word starting with "s" — e.g. `"5 samples"`, `"30 stems"`, `"2 steps"` combined with "max"/"up to" in the same text.

**Impact:** Spurious `max_duration`/`min_duration` values on `AssetRequirement`, causing the UI to enforce wrong length limits on uploaded audio.

**Fix:** `re.search(r"(\d+)\s*(?:seconds?|secs?)\b", desc_lower)`.

## LOW — `get_schema_service()` singleton is not thread-safe

**Location:** `get_schema_service` / module global `_schema_service`.

**Trigger:** Two threads calling `get_schema_service()` concurrently on first use (e.g. GUI startup + agent graph init).

**Impact:** Two `SchemaService` instances are constructed; each runs `_load_disk_cache()` and each can write the same cache files. Mostly wasted work and redundant disk I/O, but the duplicate instance also duplicates the in-memory cache, so `clear_cache()` on one instance doesn't affect the other.

**Fix:** Guard with a `threading.Lock` (double-checked locking) around the construction.

## LOW — `_apply_default_overrides` reports success even when nothing was applied

**Location:** `ReplicateSchemaProvider.fetch_schema` (`logger.info(f"Applied quality default overrides for {model_id}")`) combined with `_apply_default_overrides`.

**Trigger:** Replicate changes the response envelope (e.g. `latest_version.openapi_schema` moves/renames); the `.get()` chain silently yields empty `props`, no override is applied, no exception is raised — yet the INFO log claims overrides were applied.

**Impact:** Silent failure: the "MAXIMUM QUALITY SETTINGS" for `lucataco/ace-step` (e.g. `number_of_steps: 200`, `duration: 60`) are silently dropped while logs indicate success, making the regression undiagnosable from logs.

**Fix:** Have `_apply_default_overrides` return the count of applied overrides and log at WARNING level when `overrides` is non-empty but zero were applied.
