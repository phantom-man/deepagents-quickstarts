# Active Context

## Current Focus

**Full Media Pipeline with FFmpeg Editor - OPERATIONAL**

- Status: **All Production Agents Validated** (Cinematographer, Composer, Editor).
- Objective: End-to-end media production with zero quality loss merging.
- LangGraph Server: Running at `http://127.0.0.1:2024` via PowerShell `Start-Job`.

## Recent Changes

- **Editor FFmpeg Upgrade (2026-01-16)**:
  - **Problem**: MoviePy-only implementation re-encoded video, causing quality loss.
  - **Research**: Fetched FFmpeg, SuperUser, MoviePy documentation. Confirmed stream copy (`-c:v copy`) is gold standard.
  - **Solution**: Complete rewrite of `editor_tools.py` (~550 lines) with FFmpeg-first approach.
  - **Key Functions**: `merge_ffmpeg_stream_copy()`, `merge_ffmpeg_python()`, `concat_videos_ffmpeg()`, `quick_merge()`.
  - **Fallback Chain**: FFmpeg CLI -> ffmpeg-python -> MoviePy -> Simulation.
  - **FFmpeg Installed**: v8.0.1-full_build via `winget install ffmpeg`.
  - **Test Result**: Verified merge with test video + audio - stream copy working perfectly.
  - **Commit**: `d5df4bf` - "Upgrade editor to FFmpeg stream copy for max quality" (+426/-108 lines).

- **Video Model Migration (2026-01-16)**:
  - **Root Cause**: LangSmith Hub config had wrong video model ID (`replicate/zeroscope-v2-xl` instead of `replicate/anotherjesse/zeroscope-v2-xl`).
  - **Second Issue**: The `anotherjesse/zeroscope-v2-xl` model was deprecated/removed from Replicate (404 Not Found).
  - **Solution**: Migrated to modern `wan-video/wan-2.5-t2v-fast` model (fast, cheap, 480p-720p).
  - **Backup Model**: Added `luma/ray-flash-2-540p` as fallback.

- **Hub/Cache Synchronization Issue (2026-01-16)**:
  - **Protocol Established**: Hub is Source of Truth. Local cache is ONLY for startup speed. Check Hub first when debugging.

- **tool_choice="any" Implementation (2026-01-16)**:
  - **Solution**: Added `tool_choice="any"` to force actual tool execution, preventing hallucinations.

## Active Questions / Issues

- None critical. All core agents validated.

## Next Steps

1. **Run Model Tests**: Validate LLM, video, and audio generation end-to-end.
2. **Full Pipeline Test**: Director -> Cinematographer -> Composer -> Editor flow.
3. **Git Push**: Push all commits to remote.
