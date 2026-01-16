# Active Context

## Current Focus

**Video & Audio Generation Pipeline Validated**

- Status: **Both Cinematographer and Composer Agents Operational**.
- Objective: Full media generation pipeline with video (Wan 2.5) and audio (Lyria-002).
- LangGraph Server: Running at `http://127.0.0.1:2024` via PowerShell `Start-Job`.

## Recent Changes

- **Video Model Migration (2026-01-16)**:
  - **Root Cause**: LangSmith Hub config had wrong video model ID (`replicate/zeroscope-v2-xl` instead of `replicate/anotherjesse/zeroscope-v2-xl`).
  - **Second Issue**: The `anotherjesse/zeroscope-v2-xl` model was deprecated/removed from Replicate (404 Not Found).
  - **Solution**: Migrated to modern `wan-video/wan-2.5-t2v-fast` model (fast, cheap, 480p-720p).
  - **Backup Model**: Added `luma/ray-flash-2-540p` as fallback.
  - **Code Changes**: Updated `_generate_video()` with model-specific parameters for Wan (num_frames: 81, resolution: 480p).

- **Hub/Cache Synchronization Issue (2026-01-16)**:
  - **Problem**: Local cache file was being overwritten by outdated Hub config on every server restart.
  - **Lesson**: Hub is the Source of Truth. Local cache is only for startup speed optimization.
  - **Protocol**: When debugging model issues, ALWAYS check Hub config first, then verify local cache matches.

- **tool_choice="any" Implementation (2026-01-16)**:
  - **Problem**: Agents were hallucinating tool responses instead of actually calling tools (empty `tool_calls: []`).
  - **Solution**: Added `tool_choice="any"` to `llm.bind_tools()` for Cinematographer and Composer agents.
  - **Result**: Tools are now forced to execute, preventing text-only hallucinations.

## Active Questions / Issues

- **Editor GCS Permissions**: The Editor agent receives a 403 Forbidden when downloading videos from GCS for merging. Need to fix bucket permissions or use signed URLs.

## Next Steps

1. **Fix Editor GCS Access**: Resolve 403 errors on video download for final cut assembly.
2. **Test Full Pipeline**: Run end-to-end test with video + audio + merge.
3. **Monitor Costs**: Track Wan 2.5 and Lyria-002 usage for budget planning.
