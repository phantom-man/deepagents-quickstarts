# Active Context

## Current Focus

**LangGraph Server Running & Stable**

- Status: **Server Operational**.
- Objective: LangGraph development server accessible at `http://127.0.0.1:2024` via LangSmith Studio.
- Strategy: Use PowerShell `Start-Job` for Windows process isolation. Server takes ~50s to initialize.

## Recent Changes

- **LangGraph Server Stability (2026-01-15)**:
  - **Unicode Fix**: Fixed Windows cp1252 encoding crash by replacing all emoji characters in `hub_manager.py` with ASCII-safe alternatives (`[KEY]`, `[CACHE HIT]`, `[SUCCESS]`, `[FAILED]`, `[FALLBACK]`).
  - **Process Isolation**: Discovered that VS Code integrated terminals kill the server process on command completion. Solution: Use PowerShell `Start-Job` for background execution.
  - **Startup Time**: Server requires ~50-65 seconds due to `google.api_core._python_version_support.check_python_version()` scanning all 1,144+ packages (~26s) plus agent initialization.
  - **Prompt Caching**: Implemented disk cache in `hub_manager.py` at `.cache/prompts/` - all prompts now load from cache in milliseconds.
  - **Environment Requirement**: Must set `PYTHONIOENCODING=utf-8` on Windows.

- **Configuration Integrity (2026-01-15)**:
  - **Hub Sync**: Resolved conflict where the remote LangSmith Hub configuration (`deepagents-system-config`) was outdated (using `Claude-3-Haiku`) and overriding the local 'Truth' (`Gemini-2.0-Flash`).
  - **Voice Priority**: Updated `system_config.py` to prioritize **Google Cloud Studio Voices** (Priority 110).

## Active Questions / Issues

- **Slow Startup**: The ~50s startup time is caused by Google SDK package scanning. This is unavoidable but acceptable for development.
- **Server Watchdog**: LangGraph CLI has internal timeouts for graph loading. Current graphs load within limits but show warnings.

## Next Steps

1. **Validate Server**: Access `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`. [Ready]
2. **Test Agents**: Execute Director workflow through Studio UI.
3. **Monitor Traces**: Check LangSmith for proper Gemini-2.0-Flash traces.
