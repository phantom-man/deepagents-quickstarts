# Colibri review — DeepAgents/graphs/agency_graph.py (bug)

- source: `C:\Users\User\source\repos\deepagents-quickstarts\DeepAgents\graphs\agency_graph.py`
- model: claude-fable-5-1 (in-session Phase-3 gate over the external raw `grok-4.3` review, `.colibri_reviews/_external_raw/da__agency_graph.py__grok-4.3.md`)
- sha256: `f5957395338fb4e49a3f622d4501087fc5a9e4a7fd48fa9db42f28c941b58a9e` (current bytes at dispatch, 2026-09-05; identical to the bytes the external reviewer saw)
- date: 2026-09-05
- mode: bug
- context pack: jCodemunch symbol map + call-site search on `deepagents-quickstarts`; the external raw review; no prior `.colibri_reviews` record for this file; no remediation manifest exists in this repo. Every external finding was re-traced against the cited lines (Phase 3): CONFIRMED / PLAUSIBLE kept, refuted ones listed with the reason so they are never re-fixed (G35).

## Verdict
Not shippable: the composer node reports a false error on any single-track run whose result has no path match, and clobbers multi-track results.

## Bugs & vulnerabilities
**[HIGH] `composer_node` unbound `audio_path`/`result` and duplicate asset — CONFIRMED** - `line 1121-1136`
- Single-track: `assets.append(audio_path)` (1131) runs after `state_update` and OUTSIDE the `if match` (1121-1125). No match → `UnboundLocalError` → caught by the node's `except` (1157-1163) → the run is reported as "Audio Error" and the real result is discarded. Match → the asset is appended twice.
- Both modes: the unconditional re-assignment (1133-1136) overwrites the multi-track `state_update` (1083-1097) with "Audio Created: {last result}", and with a non-empty `tracks_config` whose entries all lack a prompt (1037-1039) `result` is unbound there too.
- Fix: delete 1131 and 1133-1136; build `state_update` once per branch, as `cinematographer_node` does.

**[LOW] `_get_comms` check-then-set on a module global — PLAUSIBLE** - `line 52-58`
- Async nodes on one loop cannot interleave inside the sync function; only Streamlit's multi-thread reruns could double-connect. Unverified because it needs the live GUI.
