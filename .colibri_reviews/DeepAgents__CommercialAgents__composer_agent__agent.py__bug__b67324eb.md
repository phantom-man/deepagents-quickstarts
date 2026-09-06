# Colibri review — DeepAgents/CommercialAgents/composer_agent/agent.py (bug)

- source: `C:\Users\User\source\repos\deepagents-quickstarts\DeepAgents\CommercialAgents\composer_agent\agent.py`
- model: claude-fable-5-1 (in-session Phase-3 gate over the external raw `grok-4.3` review, `.colibri_reviews/_external_raw/da__agent.py__grok-4.3.md`)
- sha256: `b67324ebe2230c3bdff5689208c018cc659da2384149d2cd12c3707fcd52a95f` (current bytes at dispatch, 2026-09-05; identical to the bytes the external reviewer saw)
- date: 2026-09-05
- mode: bug
- context pack: jCodemunch symbol map + call-site search on `deepagents-quickstarts`; the external raw review; no prior `.colibri_reviews` record for this file; no remediation manifest exists in this repo. Every external finding was re-traced against the cited lines (Phase 3): CONFIRMED / PLAUSIBLE kept, refuted ones listed with the reason so they are never re-fixed (G35).

## Verdict
One confirmed prompt-plumbing defect (lyrics sent as ACE-Step tags) and a temp-file leak.

## Bugs & vulnerabilities
**[MEDIUM] User-lyrics path returns no `tags`, so ACE-Step receives the full input as tags — CONFIRMED** - `line 304-307, 724, 729`
- The `has_user_lyrics` return carries `prompt` + `lyrics` only; the ACE-Step caller reads `lyric_data.get("tags", input_text)` and sends the WHOLE director text, lyrics included, in the `tags` field. Fix: return `"tags": style_prompt or "rock anthem, powerful vocals"` alongside.

**[LOW] `_download_and_validate_asset` leaves partial temp files — CONFIRMED** - `line 120, 128, 133, 140`
- Returns `None` on oversize (inside the open), too-small and exception paths without unlinking `tmp_name`.
