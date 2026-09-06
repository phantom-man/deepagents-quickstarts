# Colibri review — DeepAgents/gui/agent_runner.py (bug)

- source: `C:\Users\User\source\repos\deepagents-quickstarts\DeepAgents\gui\agent_runner.py`
- model: claude-fable-5-1 (in-session Phase-3 gate over the external raw `grok-4.3` review, `.colibri_reviews/_external_raw/da__agent_runner.py__grok-4.3.md`)
- sha256: `11752ad46b8f339536592395c48b05bcad996a3590fa28f361a1359a14008daa` (current bytes at dispatch, 2026-09-05; identical to the bytes the external reviewer saw)
- date: 2026-09-05
- mode: bug
- context pack: jCodemunch symbol map + call-site search on `deepagents-quickstarts`; the external raw review; no prior `.colibri_reviews` record for this file; no remediation manifest exists in this repo. Every external finding was re-traced against the cited lines (Phase 3): CONFIRMED / PLAUSIBLE kept, refuted ones listed with the reason so they are never re-fixed (G35).

## Verdict
Not shippable: every cinematographer run executes the paid generation twice.

## Bugs & vulnerabilities
**[HIGH] `run_cinematographer` runs the agent twice — CONFIRMED** - `line 735-784 then 786-894`
- The synchronous block creates the agent, drains its generator and yields every event; then, unconditionally, the threading block creates a SECOND agent and runs the generator again in a worker thread, yielding those events as well. Every call double-spends the generation, double-logs, and can leave inconsistent session state. The commented-out design notes (790-842) show the second block is a superseded draft — delete 785-894.

**[LOW] `poll_agent_comms` swallows every error — CONFIRMED** - `line 115-116`
- A dead DB connection ends progress updates silently.

**[LOW] `run_research_direct` has no error path — CONFIRMED** - `line 553-564`
- An exception from `run_research_task` escapes the generator with no error event.

**[LOW] `"Error" in merged_path` assumes a str — PLAUSIBLE** - `line 702`
- `merge_video_audio.invoke` return type not traced.
