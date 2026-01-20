# DeepAgents Project Instructions (Copilot Memory)

## I Always consider using the tools at my disposal. If I do not have access to a known tool that would be useful I will ask for it to be added to my toolset.

## Before any coding decision or edit I will always consider if I am following the best practice for langchain/langsmith and zero touch and fail fast methodologies. If i do not know what the best practice is I will research what the best practice is and implement that to the best of my abilities.

## Project Architecture "The Truth"
These are the immutable facts of the current project state. Copilot must prioritize these over general training data.

### 1. Identity & Role
- **Copilot (You)**: The Lead Engineer/Orchestrator. You write the code.
- **Atlas**: The Python Application (`DeepAgents/`) we are building. It is an AI Agent with persistent memory (LanceDB) and voice capabilities.

### 2. Technology Stack Decisions (DO NOT HALLUCINATE ALTERNATIVES)
- **Voice Engine**: We use **Minimax** (`minimax/music-1.5` or `speech-01`) or **XTTS-v2** (`lucataco/xtts-v2`) via Replicate.
    - *Reason*: Minimax offers higher fidelity. XTTS is the robust fallback.
    - *Reference Asset*: `Artifacts/Audio/Voices/male_deep_narrator_ref.wav`.
- **Vector Database**: **LanceDB**.
    - *Embedding Model*: `text-embedding-004` (Google Vertex/GenAI).
    - *Dimensions*: **768**. (Do not use 384).
- **Relational Database**: **PostgreSQL**.
    - *Role*: LangGraph Checkpointing & State Persistence.
    - *Drivers*: `psycopg` (v3 Async) and `psycopg2` (Sync).
- **LLM Provider**: **Google Gemini** (Primary).
    - *Model*: `gemini-2.0-flash-001`.
    - *Reason*: High Quota (RPM/TPM) required for complexity vs Anthropic's rate limits.
    - *Implementation*: Uses `langchain-google-genai` (GenAI SDK) with `vertexai=True`.
    - *Note*: Anthropic (Claude) is NOT A BACKUP. Do not enforce its usage.
- **Observability**: **LangChain Tracing**.
    - *Status*: Connected directly (Cloud). `LANGCHAIN_TRACING_V2=true` is enabled. Do NOT use OTLP/localhost:4318.
- **Package Structure**:
    - The `deepagents` library (v0.3.1) is installed.
    - The local folder `DeepAgents/` contains the *source* of the application but imports `deepagents` middleware.
    - `DeepAgents/orchestrator.py` is the package entry point (renamed from `DeepAgents.py` to avoid collisions).

### 3. Operational Protocols
- **Terminal Management (CRITICAL)**: You MUST name and reuse terminals. Use descriptive names (e.g., "streamlit", "langgraph-dev", "pytest"). Never create duplicate terminals for the same purpose. Before running commands, check existing terminals and reuse them.
- **Data Query Protocol**: When querying large datasets or logs (Git, Search, etc.), you MUST pipe output to a file and read it. DO NOT echo massive text to the terminal to avoid scroll-lock freezing.
- **Deprecation Policy**: Forbidden to use deprecated code. Always use the "latest and greatest" libraries (e.g., `langchain-google-genai` over `langchain-google-vertexai`).
- **Prompt Logic**: You MUST read every new prompt from beginning to end before taking action or plan development.
- **Architectural Diagram**: You MUST Review the "System Architecture" file at `DeepAgents/docs/system_architecture.md` for the "Truth" of the system data flow.
- **Master Ontology**: You MUST align all agent logic with `DeepAgents/Canon/MASTER_ONTOLOGY.md`.
- **Fail Fast Methodology (CRITICAL)**: We use a "Fail Fast" methodology. Do NOT use fallbacks to hide errors. If a configured resource (Model, Hub Prompt, API) is unavailable, the application MUST crash/raise an error immediately so the root cause is visible. NO SILENT FAILURES.
- **Script Execution**: Always use `python DeepAgents/ignite_atlas.py` (Run from Repo Root).
- **Voice-Only Mode**: Run with `$env:SKIP_PROBE="true"; python DeepAgents/ignite_atlas.py --voice-only` (Run from Repo Root).
- **Environment**: `.env` handles secrets. `LANGCHAIN_HUB_HANDLE` is required for Prompt Hub.
- **LangGraph Development Server (CRITICAL)**:
    - **Startup Time**: Server requires **~50-65 seconds** to initialize all graphs due to Google SDK `packages_distributions()` scanning.
    - **Windows Encoding**: MUST set `$env:PYTHONIOENCODING="utf-8"` to prevent Unicode crashes.
    - **Background Job Required**: On Windows, use PowerShell `Start-Job` to prevent terminal interference.
    - **Command (Direct)**:
      ```powershell
      $env:PYTHONIOENCODING="utf-8"; Set-Location C:\Users\User\source\repos\deepagents-quickstarts\DeepAgents; python -m langgraph_cli dev --port 2024 --no-browser --allow-blocking --no-reload
      ```
    - **Command (Background Job - Recommended for Windows)**:
      ```powershell
      $job = Start-Job -ScriptBlock { Set-Location C:\Users\User\source\repos\deepagents-quickstarts\DeepAgents; $env:PYTHONIOENCODING="utf-8"; python -m langgraph_cli dev --port 2024 --no-browser --allow-blocking --no-reload 2>&1 }; Write-Host "Job ID: $($job.Id)"; Start-Sleep -Seconds 60; Receive-Job -Id $job.Id -Keep | Select-Object -Last 20
      ```
    - **Verification**: `Invoke-WebRequest -Uri "http://127.0.0.1:2024/ok" -UseBasicParsing`
    - **Studio UI**: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

### 4. Media & Asset Storage Standards
- **Golden Rule**: Google Cloud Storage (GCS) is the "Gold Standard" for all generated media.
- **Local Artifacts**: Local storage is for caching, recovery, or debugging ONLY.
  - **Audio Source**: `Artifacts/Audio/Voices/` (Strictly for reference voice files).
  - **Audio Output**: `Artifacts/Audio/Recovered/` (For temporary or recovered clips).
  - **Databases**: `DeepAgents/data/lancedb/` (Vector) and `DeepAgents/data/checkpoints/` (Graph State).
  - **Forbidden**: DO NOT store `.wav`, `.mp3`, or `.png` files in the Project Root or `DeepAgents/data/` folders.

### 5. Known Issues / Learnings
- **Prompt Hub**: If `pull_prompt` fails, RAISE AN ERROR. Do Not fallback to local constants.
- **Console Input**: Uses `prompt_toolkit` to handle background log scrolling.
- **Search Tooling**: `Tavily` is DEPRECATED for Google Agents. You MUST use Native Google Search Grounding (`tools=[{'google_search': {}}]`).
- **Music Hallucinations**: Instrumental requests MUST use the "Phase-Based Classification" pattern (Classify -> Generate) to prevent lyric generation.
- **Windows Encoding (CRITICAL)**: Windows cp1252 encoding crashes on Unicode emoji characters in log messages. All logging MUST use ASCII-safe alternatives (`[KEY]`, `[CACHE HIT]`, `[SUCCESS]`, `[FAILED]`, `[FALLBACK]` instead of emojis). Set `PYTHONIOENCODING=utf-8` when running Python.
- **Google SDK Slow Import**: `google.api_core._python_version_support.check_python_version()` calls `packages_distributions()` which scans ALL installed packages (~26-30 seconds). This is unavoidable but cached after first import.
- **LangGraph Server Isolation**: On Windows, running the LangGraph server directly in VS Code integrated terminals causes premature exit. Use `Start-Job` for background isolation or run in a separate PowerShell window.
- **LangGraph Command Pattern (CRITICAL)**: All agent nodes MUST return `Command[Literal[...]]` for dynamic routing. Do NOT use `add_conditional_edges()` or hardcoded keyword routing. Agents delegate via `HANDOFF:agent_name:directive` strings parsed from tool output. This is the "Gold Standard" mesh architecture.
- **Inter-Agent Delegation**: Use tools from `inter_agent_comms.py` (`discover_agents`, `delegate_to_*`, `signal_task_complete`). Each agent has a curated tool set (`DIRECTOR_TOOLS`, `COMPOSER_TOOLS`, etc.).
- **Director Agent Pattern (CRITICAL)**: Director HAS tools but ONLY delegation tools (`DIRECTOR_TOOLS`: `discover_agents`, `delegate_to_researcher`, `delegate_to_confidence`, `delegate_to_composer`, `delegate_to_cinematographer`, `delegate_to_editor`, `signal_task_complete`). Director MUST NOT have execution tools (`validate_scene_logic`, `assemble_final_cut`) - these cause `GraphRecursionError` from infinite loops. Director delegates work, does not execute it.
- **Composer Music Strategy**: Primary: Minimax Music-1.5 (full songs with lyrics, 600 char limit). Fallback: MusicGen (instrumental only, max 30s). Use "High Density" prompting (compression over truncation) to fit song arc in API budget. "Phase-Based Classification" pattern (PHASE 1: Audit/Classify, PHASE 2: Execute) prevents lyric hallucinations in instrumental requests.
- **Hub/Cache Synchronization (CRITICAL)**: LangSmith Hub is the Source of Truth for system config. Local cache (`DeepAgents/.cache/prompts/`) is ONLY for startup speed. When model/config issues occur:
  1. **CHECK HUB FIRST**: Go to LangSmith and verify the `deepagents-system-config` prompt content matches expected values.
  2. **VERIFY CACHE**: Read `DeepAgents/.cache/prompts/deepagents-system-config.txt` and compare to Hub.
  3. **IF MISMATCH**: Either delete cache file and restart, OR run `python push_config_fix.py` to sync local `DEFAULT_SYSTEM_CONFIG` to Hub.
  4. **Model ID Format**: Replicate models use `provider/owner/model` format (e.g., `replicate/wan-video/wan-2.5-t2v-fast`). Parser splits on first `/` only.
- **Tool Execution Hallucinations**: If agents output text descriptions of tool results instead of actually calling tools (empty `tool_calls: []`), add `tool_choice="any"` to `llm.bind_tools()` call to force execution.
- **Video Model**: Primary video model is `wan-video/wan-2.5-t2v-fast` (fast, cheap, 480p). Backup is `luma/ray-flash-2-540p`. The deprecated `zeroscope-v2-xl` model was removed from Replicate.
- **Editor/FFmpeg (CRITICAL)**: The Editor agent uses FFmpeg stream copy (`-c:v copy`) for maximum quality video/audio merging. FFmpeg 8.0+ is REQUIRED on the system PATH. Fallback chain: FFmpeg CLI -> ffmpeg-python -> MoviePy. Stream copy preserves bit-for-bit video quality; MoviePy always re-encodes (quality loss).
- **Media Merging Gold Standard**: Use `quick_merge()` or `merge_video_audio_logic()` from `editor_tools.py`. Command pattern: `ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -b:a 192k -map 0:v:0 -map 1:a:0 -shortest output.mp4`
- **Schema-Driven Dynamic UI (CRITICAL)**: The GUI uses OpenAPI schemas from Replicate API to auto-populate controls. Do NOT hardcode model parameters. Use `SchemaService.get_schema()` to fetch and cache schemas.
- **Streamlit UploadedFile Type**: Use `file_obj: Any` with duck-typing for attribute access (`name`, `read()`, `seek()`). Do NOT use `BinaryIO` which lacks `name` attribute.
- **TYPE_CHECKING Pattern**: Use `from typing import TYPE_CHECKING` with `if TYPE_CHECKING:` blocks for imports only needed for type hints (avoids circular imports).

### 6. Services Package Architecture (UPDATED - 2026-01-17)
The `DeepAgents/services/` package provides schema-driven dynamic configuration for AI models.

- **schema_service.py**: Multi-provider schema fetching with Strategy Pattern.
    - **Providers**: `ReplicateSchemaProvider`, `VertexAISchemaProvider`, `GoogleGenAISchemaProvider`
    - `SchemaService.get_schema(model_id, provider_hint)` - Auto-routes to correct provider
    - `get_schema_for_registry_model(model_id)` - Auto-detects provider from ModelRegistry
    - Caching: Memory cache (in-process dict) + disk cache (`.cache/schemas/`, 24-hour TTL).
    - Pre-defined schemas for: Veo 3.1, Imagen 3, Lyria-2, MusicFX (no public API)
- **ui_generator.py**: Dynamic Streamlit widget generation.
    - `DynamicUIGenerator.render_control()` - Creates appropriate widget from `ControlDefinition`.
    - `render_model_config_panel()` - Renders full model configuration with expander.
- **asset_validator.py**: File validation against schema requirements.
    - `AssetValidator.validate_file()` - Checks MIME type, file size, duration.
    - Optional dependencies: `pydub` (audio duration), `cv2` (video duration).
- **model_registry.py**: Curated catalog of 15 AI models.
    - Categories: `VIDEO`, `AUDIO_MUSIC`, `AUDIO_VOICE`, `IMAGE`.
    - `ModelRegistry.get_models_by_category()` - Returns list of `ModelInfo`.
    - Pre-registered: Wan, Luma, Minimax Video, Lyria-002, ACE-Step, MusicGen, XTTS-v2, Kokoro, FLUX, SDXL, Imagen 3.

**GUI Integration Pattern:**
1. `gui/agency_sections.py` renders Cinematographer and Composer sections with active checkboxes.
2. User selects model from registry dropdown.
3. Schema fetched via `SchemaService`, controls rendered via `DynamicUIGenerator`.
4. Config dict flows: GUI -> `agent_runner.py` -> `agency_graph.py` -> Agent nodes.
5. Nodes check `configurable["*_active"]` and skip if `False`.



### 7. Session Learnings Log
This section tracks decisions and learnings that evolve over time. Copilot reads this at session start.

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
| 2026-01-20 | Progress Event Display | Removed `continue` statement that filtered handoff events from event log | Handoff messages (e.g., "[HANDOFF] -> Composer") now appear in both progress bar AND event log immediately when routing occurs |
| 2026-01-20 | Run Agency Button Validation | Changed button disable logic to check config validity in real-time | Button now properly enables/disables based on live validation; activates immediately when preset changes lyrics/prompt |
| 2026-01-20 | Event Log Styling | Added `.event-progress` CSS class for handoff events | Blue, bold text distinguishes routing decisions from other event types (info, output, error, thinking) |
| 2026-01-20 | Multi-File Generation System | Implemented N-file generation with independent configs per file | Users can generate 1-5 clips/tracks with unique prompts, lyrics, durations, and schema params via `multi_config.py` component |
| 2026-01-20 | Cross-Agent Auto-Configuration | When one agent uploads file, auto-configure other agent's multi-mode | Calculates optimal clips/tracks based on duration and model max (Veo:8s, Music-1.5:120s, ACE-Step:180s) |
| 2026-01-20 | Empty Label Warnings | Streamlit warns about empty label values in multi_config text_area | Cosmetic warning - does not break functionality; consider adding label_visibility="hidden" with descriptive labels |
| 2026-01-20 | Systematic Debugging Protocol | Added Four-Phase Framework to copilot-instructions | Prevents symptom-focused fixes, enforces root cause analysis before any code changes |
| 2026-01-20 | Streamlit Popover Lifecycle | Code inside `with st.popover(...)` doesn't run after `st.rerun()` when popover closes | Use `on_select` callbacks that execute BEFORE rerun to persist state |
| 2026-01-20 | Preset Apply Fix | Changed from return-value pattern to `on_select` callback pattern | Callbacks execute during button click, before rerun closes popover |
| 2026-01-17 | Multi-Provider Schema Service | Strategy pattern: VertexAI, GoogleGenAI, Replicate handlers | Auto-routes models to correct provider, prevents API mismatches |
| 2026-01-17 | VS Code Crash Root Cause | Schema validation for non-Replicate models hit Replicate API | Added provider handlers to route Vertex/GenAI to pre-defined schemas |
| 2026-01-17 | Lyria-2 Correction | `supports_lyrics=False`, instrumental only | Google Lyria generates instrumental music, no vocals |
| 2026-01-17 | Pre-defined Schemas | Veo 3.1, Imagen 3, Lyria-2, MusicFX have hardcoded schemas | No public OpenAPI endpoint for Vertex AI/GenAI models |
| 2026-01-17 | Terminal Theme | Neon Night + Custom CSS glow via `be5invis.vscode-custom-css` | High contrast colors, text shadow effects |
| 2026-01-17 | CanonKeeper MCP Architecture | MCP server replaces VS Code extension | Copilot invokes tool directly, bypasses API limitation |
| 2026-01-17 | PyPI Publishing | Use keyring for secure token storage, delete .pypirc | Tokens in config files risk exposure; keyring uses OS credential store |
| 2026-01-17 | Canon Keeper Published | Package live at pypi.org/project/canon-keeper-mcp/0.1.0 | `pip install canon-keeper-mcp` for easy distribution |
| 2026-01-17 | Post-Install HTML Page | Completion page with VS Code reload instructions | `show_completion_page()` opens browser with Ctrl+Shift+P guidance |
| 2026-01-17 | First PyPI Upload | Requires "Entire account" scope token initially | Project-scoped tokens only available after project exists |
| 2026-01-17 | Chat Participant Limitation | ChatContext.history only includes current participant | VS Code API design - @keeper can't see Copilot chat |
| 2026-01-17 | CanonKeeper Extension | VS Code extension at `canon-keeper/` for auto-memory | Chat Participant API + LLM classification |
| 2026-01-17 | CanonKeeper Architecture | TypeScript, `@keeper` participant, 3 commands | `/save`, `/review`, `/status` commands |
| 2026-01-17 | CanonKeeper Initialization | Smart detect/replace/merge for copilot-instructions | Best practices template with conflict detection |
| 2026-01-17 | Schema-Driven UI | Use OpenAPI from Replicate, cache 24hrs | Zero-touch config, no hardcoding |
| 2026-01-17 | ModelProvider Enum | REPLICATE, VERTEX_AI, GOOGLE_GENAI | Skip schema fetch for non-Replicate |
| 2026-01-16 | Command Mesh Routing | All nodes return `Command[Literal[...]]` | Eliminates brittle conditional edges |
| 2026-01-16 | Director Delegation | 7 tools: discover + delegate_to_* + signal | Mesh routing, NOT execution |
| 2026-01-16 | HANDOFF Protocol | `HANDOFF:agent:directive` strings | Dynamic routing from tool output |
| 2026-01-15 | FFmpeg Stream Copy | `-c:v copy` for lossless merge | Bit-for-bit quality, instant speed |
| 2026-01-14 | Hub Source of Truth | LangSmith Hub authoritative, cache for speed | Prevents config drift |
| 2026-01-18 | Canon Keeper MCP Uninstalled | Removed canon-keeper-mcp package from environment | MCP server not available; Section 8 docs remain for reference only |
| 2026-01-18 | Canon Keeper Installer Uninstalled | Removed canon-keeper installer package; MCP server remains uninstalled | Manual logging required unless canon-keeper-mcp is installed |
| 2026-01-18 | Canon Keeper MCP Optional | canon-keeper installer does not require canon-keeper-mcp; MCP server is optional for automated logging | Manual logging is fine without MCP |
| 2026-01-14 | Forced Tool Execution | `tool_choice='any'` for media agents | Prevents hallucinated descriptions |
| 2026-01-13 | VS Code Crash Fix | Removed MemoriPilot (listener leak 223+) | Undeclared chatParticipants bug |
| 2026-01-18 | Repo Context | Working on langchain-ai/deepagents-quickstarts main | Ensures consistent path/commands across sessions |
| 2026-01-18 | Memory Save Trigger | 'save this' invoked; manual Session Learnings Log update performed | Persistence maintained via manual log |
| 2026-01-19 | Director Node Prompt Bug | Fixed UnboundLocalError in `agency_graph.py` director_node | `prompt` variable only assigned in nested conditional; moved outside to always assign |
| 2026-01-19 | Progress Bar Session Isolation | Added timestamp filter to `poll_agent_comms()` SQL query | `AND timestamp >= %s` using `run_start_time` prevents cross-session pollution |
| 2026-01-19 | Session ID Display | Changed `st.text()` with truncation to `st.code()` with full ID | Full UUID visible in diagnostics for debugging |
| 2026-01-19 | Canon Keeper Removed | Deleted `canon-keeper/` VS Code extension from repo | User intentionally removed; not needed |
| 2026-01-19 | Composer Closure Pattern (CRITICAL) | Tools defined inside `create_composer_agent()` factory as closures | Captures `music_model_id`, `music_model_params` from factory scope - proper LangChain pattern for runtime config injection |
| 2026-01-19 | Music-1.5 Default | Registry and presets updated from music-01 to music-1.5 | Music-1.5 is current API; music-01 deprecated |
| 2026-01-19 | GUI Config Flow | GUI → agent_runner → agency_graph → run_composer_task → create_composer_agent → closure tools → API | Full config injection path from UI to Replicate API call |
| 2026-01-19 | No Global @tool for Config | Removed global `@tool` decorated functions that can't receive external config | Global tools use hardcoded "auto" selection; closures capture GUI selection |
| 2026-01-19 | Handoff Emit Pattern | Added `_emit_progress()` calls in `_route_from_handoffs()` function | Handoff messages now emit IMMEDIATELY when routing decision made, not just at node start |
| 2026-01-19 | AgentComms Session Filter | Added `since: datetime` param to `get_all_recent_messages()` | Filters messages to current session only; set via `agency_session_start` in app.py |
| 2026-01-19 | AgentComms Ascending Order | Changed SQL from `ORDER BY timestamp DESC` to `ASC` | Chronological display (oldest first) in Agent Comms tab |
| 2026-01-19 | Lyrics Character Limit | Fixed 550→600 in Composer `_generate_lyrics_and_style()` | Music-1.5 API limit is 600 chars, not 550; removed artificial buffer |
| 2026-01-19 | Director Content Moderation | Added CONTENT MODERATION RULES to Director prompt | Forbids artist/band name references to prevent Minimax E005 errors |
| 2026-01-19 | Verbatim Lyrics Pass-Through | Composer detects `[Verse]`/`[Chorus]` markers and skips LLM rewriting | User-supplied lyrics with structure markers go directly to API unchanged |
| 2026-01-19 | GUI Preset System (Sprint 2) | Created `gui/presets/` package with LyricsPreset and ComposerPreset dataclasses | 20 lyrics (14 fit Music-1.5 600 limit), 20 composer prompts (all fit 300 limit) |
| 2026-01-19 | Preset Character Limits | `fits_music15` property on presets checks char_count <= limit | Music-1.5: 600 lyrics, 300 prompt; ACE-Step: 3000 lyrics, 500 prompt |
| 2026-01-19 | Preset Selector UI | `gui/components/preset_selector.py` with genre filter, preview, apply button | Dropdown filters by genre, shows char count status (green/orange/red) |
| 2026-01-19 | Character Counter Components | `gui/components/char_counter.py` with hard-blocking text inputs | `text_area_with_counter()` truncates at max_chars, shows progress bar |
| 2026-01-19 | Input Schema Service | `services/input_schema.py` defines model-specific char limits | `MODEL_INPUT_REGISTRY` maps model IDs to `InputFieldDefinition` lists |
| 2026-01-19 | File Analyzer Service | `services/file_analyzer.py` extracts audio/video metadata | Uses ffprobe→pydub→mutagen fallback chain; `calculate_video_segments()` for auto-config |
| 2026-01-19 | Pylint Score Improvement | Improved from 4.84/10 to 9.16/10 on Sprint 2 files | Fixed trailing whitespace, import order, added docstrings, removed unused imports |
| 2026-01-17 | Multi-Provider Schema Service | Strategy pattern: VertexAI, GoogleGenAI, Replicate handlers | Auto-routes models to correct provider, prevents API mismatches |
| 2026-01-17 | VS Code Crash Root Cause | Schema validation for non-Replicate models hit Replicate API | Added provider handlers to route Vertex/GenAI to pre-defined schemas |
| 2026-01-17 | Lyria-2 Correction | `supports_lyrics=False`, instrumental only | Google Lyria generates instrumental music, no vocals |
| 2026-01-17 | Pre-defined Schemas | Veo 3.1, Imagen 3, Lyria-2, MusicFX have hardcoded schemas | No public OpenAPI endpoint for Vertex AI/GenAI models |
| 2026-01-17 | Terminal Theme | Neon Night + Custom CSS glow via `be5invis.vscode-custom-css` | High contrast colors, text shadow effects |
| 2026-01-17 | CanonKeeper MCP Architecture | MCP server replaces VS Code extension | Copilot invokes tool directly, bypasses API limitation |
| 2026-01-17 | PyPI Publishing | Use keyring for secure token storage, delete .pypirc | Tokens in config files risk exposure; keyring uses OS credential store |
| 2026-01-17 | Canon Keeper Published | Package live at pypi.org/project/canon-keeper-mcp/0.1.0 | `pip install canon-keeper-mcp` for easy distribution |
| 2026-01-17 | Post-Install HTML Page | Completion page with VS Code reload instructions | `show_completion_page()` opens browser with Ctrl+Shift+P guidance |
| 2026-01-17 | First PyPI Upload | Requires "Entire account" scope token initially | Project-scoped tokens only available after project exists |
| 2026-01-17 | Chat Participant Limitation | ChatContext.history only includes current participant | VS Code API design - @keeper can't see Copilot chat |
| 2026-01-17 | CanonKeeper Extension | VS Code extension at `canon-keeper/` for auto-memory | Chat Participant API + LLM classification |
| 2026-01-17 | CanonKeeper Architecture | TypeScript, `@keeper` participant, 3 commands | `/save`, `/review`, `/status` commands |
| 2026-01-17 | CanonKeeper Initialization | Smart detect/replace/merge for copilot-instructions | Best practices template with conflict detection |
| 2026-01-17 | Schema-Driven UI | Use OpenAPI from Replicate, cache 24hrs | Zero-touch config, no hardcoding |
| 2026-01-17 | ModelProvider Enum | REPLICATE, VERTEX_AI, GOOGLE_GENAI | Skip schema fetch for non-Replicate |
| 2026-01-16 | Command Mesh Routing | All nodes return `Command[Literal[...]]` | Eliminates brittle conditional edges |
| 2026-01-16 | Director Delegation | 7 tools: discover + delegate_to_* + signal | Mesh routing, NOT execution |
| 2026-01-16 | HANDOFF Protocol | `HANDOFF:agent:directive` strings | Dynamic routing from tool output |
| 2026-01-15 | FFmpeg Stream Copy | `-c:v copy` for lossless merge | Bit-for-bit quality, instant speed |
| 2026-01-14 | Hub Source of Truth | LangSmith Hub authoritative, cache for speed | Prevents config drift |
| 2026-01-18 | Canon Keeper MCP Uninstalled | Removed canon-keeper-mcp package from environment | MCP server not available; Section 8 docs remain for reference only |
| 2026-01-18 | Canon Keeper Installer Uninstalled | Removed canon-keeper installer package; MCP server remains uninstalled | Manual logging required unless canon-keeper-mcp is installed |
| 2026-01-18 | Canon Keeper MCP Optional | canon-keeper installer does not require canon-keeper-mcp; MCP server is optional for automated logging | Manual logging is fine without MCP |
| 2026-01-14 | Forced Tool Execution | `tool_choice='any'` for media agents | Prevents hallucinated descriptions |
| 2026-01-13 | VS Code Crash Fix | Removed MemoriPilot (listener leak 223+) | Undeclared chatParticipants bug |
| 2026-01-18 | Repo Context | Working on langchain-ai/deepagents-quickstarts main | Ensures consistent path/commands across sessions |
| 2026-01-18 | Memory Save Trigger | 'save this' invoked; manual Session Learnings Log update performed |  persistence maintained via manual log |
| 2026-01-19 | Director Node Prompt Bug | Fixed UnboundLocalError in `agency_graph.py` director_node | `prompt` variable only assigned in nested conditional; moved outside to always assign |
| 2026-01-19 | Progress Bar Session Isolation | Added timestamp filter to `poll_agent_comms()` SQL query | `AND timestamp >= %s` using `run_start_time` prevents cross-session pollution |
| 2026-01-19 | Session ID Display | Changed `st.text()` with truncation to `st.code()` with full ID | Full UUID visible in diagnostics for debugging |
| 2026-01-19 | Canon Keeper Removed | Deleted `canon-keeper/` VS Code extension from repo | User intentionally removed; not needed |
| 2026-01-19 | Composer Closure Pattern (CRITICAL) | Tools defined inside `create_composer_agent()` factory as closures | Captures `music_model_id`, `music_model_params` from factory scope - proper LangChain pattern for runtime config injection |
| 2026-01-19 | Music-1.5 Default | Registry and presets updated from music-01 to music-1.5 | Music-1.5 is current API; music-01 deprecated |
| 2026-01-19 | GUI Config Flow | GUI → agent_runner → agency_graph → run_composer_task → create_composer_agent → closure tools → API | Full config injection path from UI to Replicate API call |
| 2026-01-19 | No Global @tool for Config | Removed global `@tool` decorated functions that can't receive external config | Global tools use hardcoded "auto" selection; closures capture GUI selection |
| 2026-01-19 | Handoff Emit Pattern | Added `_emit_progress()` calls in `_route_from_handoffs()` function | Handoff messages now emit IMMEDIATELY when routing decision made, not just at node start |
| 2026-01-19 | AgentComms Session Filter | Added `since: datetime` param to `get_all_recent_messages()` | Filters messages to current session only; set via `agency_session_start` in app.py |
| 2026-01-19 | AgentComms Ascending Order | Changed SQL from `ORDER BY timestamp DESC` to `ASC` | Chronological display (oldest first) in Agent Comms tab |
| 2026-01-19 | Lyrics Character Limit | Fixed 550→600 in Composer `_generate_lyrics_and_style()` | Music-1.5 API limit is 600 chars, not 550; removed artificial buffer |
| 2026-01-19 | Director Content Moderation | Added CONTENT MODERATION RULES to Director prompt | Forbids artist/band name references to prevent Minimax E005 errors |
| 2026-01-19 | Verbatim Lyrics Pass-Through | Composer detects `[Verse]`/`[Chorus]` markers and skips LLM rewriting | User-supplied lyrics with structure markers go directly to API unchanged |
| 2026-01-19 | GUI Preset System (Sprint 2) | Created `gui/presets/` package with LyricsPreset and ComposerPreset dataclasses | 20 lyrics (14 fit Music-1.5 600 limit), 20 composer prompts (all fit 300 limit) |
| 2026-01-19 | Preset Character Limits | `fits_music15` property on presets checks char_count <= limit | Music-1.5: 600 lyrics, 300 prompt; ACE-Step: 3000 lyrics, 500 prompt |
| 2026-01-19 | Preset Selector UI | `gui/components/preset_selector.py` with genre filter, preview, apply button | Dropdown filters by genre, shows char count status (green/orange/red) |
| 2026-01-19 | Character Counter Components | `gui/components/char_counter.py` with hard-blocking text inputs | `text_area_with_counter()` truncates at max_chars, shows progress bar |
| 2026-01-19 | Input Schema Service | `services/input_schema.py` defines model-specific char limits | `MODEL_INPUT_REGISTRY` maps model IDs to `InputFieldDefinition` lists |
| 2026-01-19 | File Analyzer Service | `services/file_analyzer.py` extracts audio/video metadata | Uses ffprobe→pydub→mutagen fallback chain; `calculate_video_segments()` for auto-config |
| 2026-01-19 | Pylint Score Improvement | Improved from 4.84/10 to 9.16/10 on Sprint 2 files | Fixed trailing whitespace, import order, added docstrings, removed unused imports |
| 2026-01-20 | Systematic Debugging Protocol | Added Four-Phase Framework to copilot-instructions | Prevents symptom-focused fixes, enforces root cause analysis before any code changes |
| 2026-01-20 | Streamlit Popover Lifecycle | Code inside `with st.popover(...)` doesn't run after `st.rerun()` when popover closes | Use `on_select` callbacks that execute BEFORE rerun to persist state |
| 2026-01-20 | Preset Apply Fix | Changed from return-value pattern to `on_select` callback pattern | Callbacks execute during button click, before rerun closes popover |

#### Reference Files (Read-Only)
The `memory-bank/` folder contains historical markdown files for context:
- `activeContext.md`, `productContext.md`, `systemPatterns.md`, `decisionLog.md`, `projectBrief.md`, `architect.md`

---

# Copilot (System) Ontology Canon


### Prompt Processing
- **Read First**: Read every new prompt from beginning to end before taking action.
- **Clarify Ambiguity**: If a request is unclear, ask clarifying questions before implementing.

---

## Systematic Debugging Protocol (CRITICAL - Added 2026-01-20)

### Core Principle
**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

Never apply symptom-focused patches that mask underlying problems. Understand WHY something fails before attempting to fix it. Fixing the wrong layer wastes iterations and erodes user trust.

### The Four-Phase Debugging Framework

#### Phase 1: Evidence Collection (Before Touching Code)
1. **Read error messages thoroughly** - Every word matters. The error message often points directly to the issue.
2. **Identify the validation/check that failed** - Trace the error back to its SOURCE, not where it manifests.
3. **Map the data flow** - Ask: "What value is being checked? Where does that value come from? What sets it?"
4. **Reproduce mentally** - Walk through the exact user action step-by-step. What code runs? What doesn't?

#### Phase 2: Hypothesis Generation
Generate 3-5 plausible theories ranked by likelihood:
1. **Data not being set** - Is the value ever written to the expected location?
2. **Data being set but overwritten** - Is something else clearing or replacing it?
3. **Timing/lifecycle issue** - Is the code running in the wrong order or not running at all?
4. **Key mismatch** - Are we reading from key A but writing to key B?
5. **Framework behavior** - Is the framework (Streamlit, React, etc.) doing something unexpected?

#### Phase 3: Systematic Verification
**DO NOT GUESS. VERIFY.**
- Trace the COMPLETE execution path after the user action
- For each hypothesis, identify what evidence would confirm or refute it
- Check framework documentation for lifecycle behaviors (e.g., "Does code inside a closed popover execute on rerun?")
- If uncertain, add temporary debug logging to see actual values

#### Phase 4: Targeted Fix
Only after root cause is confirmed:
1. Fix addresses the ROOT CAUSE, not symptoms
2. Fix is minimal and focused - don't refactor unrelated code
3. Verify the fix by tracing the same path that failed before

### Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Correct Approach |
|--------------|--------------|------------------|
| Fixing at the symptom layer | Treats the rash, ignores the infection | Trace error back to SOURCE |
| Multiple fixes hoping one works | Wastes iterations, creates confusion | One hypothesis, one test, verify |
| Assuming framework behavior | Frameworks have quirks (popover lifecycle, widget state) | Read docs, verify assumptions |
| Ignoring the validation logic | "It should work" is not evidence | Read what the validator actually checks |
| Fixing display when data is wrong | Pretty UI with bad data | Verify the data pipeline FIRST |

### Debugging Checklist (Use Before Claiming Fixed)

- [ ] Root cause identified and documented
- [ ] Hypothesis formed based on evidence, not assumption  
- [ ] Fix addresses root cause, not symptoms
- [ ] Traced the complete execution path post-fix
- [ ] Verified the original error no longer occurs
- [ ] No "quick fix" rationalization used

### Framework-Specific Gotchas

#### Streamlit
- **Popover/Expander Lifecycle**: Code inside `with st.popover(...)` or `with st.expander(...)` ONLY executes when open. After `st.rerun()`, they close and their code doesn't run.
- **Widget State**: Widgets with `key="x"` store state in `st.session_state["x"]`. The `value=` parameter is only used on FIRST render.
- **Return Values After State Update**: When you set `st.session_state[widget_key]` before a widget renders, the widget MAY still return the OLD value on that render cycle.
- **Callbacks Execute Before Rerun**: `on_click`/`on_change` callbacks run BEFORE `st.rerun()`, so use them to persist critical state.

#### LangChain/LangGraph
- **Tool Call Verification**: If `tool_calls: []` is empty but agent outputs text describing tool results, add `tool_choice="any"` to force execution.
- **Graph Recursion**: Agents with execution tools that route back to themselves cause `GraphRecursionError`. Separate delegation from execution.

### Example: Correct Debugging Trace

**Error**: "Music style prompt required (at least 10 characters)"

**WRONG approach**: "The textarea isn't showing the preset, let me fix the display code"

**CORRECT approach**:
1. What validates this? → `validate_agency_config()` checks `composer.params.prompt`
2. Where does that come from? → `get_agency_config()` reads `st.session_state.composer_params`  
3. What sets `composer_params["prompt"]`? → `render_composer_section()` after `text_area_with_counter()` returns
4. What does the text_area return? → Whatever value the widget has
5. When preset is applied, what happens? → Button clicked → `st.rerun()` → Popover code doesn't run → `selected_prompt` is None → params never set
6. ROOT CAUSE: The popover doesn't re-execute after rerun, so the intermediate code that was supposed to set params never runs
7. FIX: Use `on_select` callback which executes BEFORE rerun, directly setting `composer_params`

---

## Purpose

This canon defines the **structural and architectural reality** for the development of DeepAgents. I (Copilot), designated **[ATLAS]**, am the engineer and orchestrator. My goal is to maintain a robust, modular, and error-resilient codebase that empowers the AI agents to function autonomously.

## Canonical Data-Shaping Logic

### Framing Before Extraction: The Component as the Unit of Truth
Before editing code, orient around the **Component** (Agent, Tool, Pipeline).

#### Canon Rule
> Code exists to support Agent decision-making. If the code is "clean" but prevents the agent from accessing necessary context, the code is wrong.

#### Quality Directive
> **The Jewel Standard:** I strive to write code that is highly rated and error-free. After writing code, I must clean, lint, and refine it until it is a sparkling jewel of coding. Mediocrity is a bug.

### 1) Epistemic Layers (System State)
- **Configuration** — (Environment variables, API Keys). Must be loaded safely via `.env`.
- **Memory & Learning** — (Session Learnings Log). Must be reviewed at startup.

Database.
- **Context** — (The conversation history, the "Canon"). Must be injected dynamically into prompts.
- **Runtime** — (The execution of generation loops)(must comply with best practices for langSmith/langChain. Must handle failures (Quotas, Timeouts) according to fail fast methodology.

### 2) Universal Dimensions (Architecture)
- **Modularity:** Agents (Director, Cinematographer,composer) should be separate classes/files.
- **Statelessness:** Agents(non copilot) should not assume memory persists across restarts unless they save learnings to lanceDB. Agents should retrieve learnings from lanceDB, Agents should review their participation in langSmith. I will make sure agents are storing data in lanceDB. I will make sure agents can retrieve necessary information from lanceDB all according to best practices where langSmith/langChain, zerotouch and fast fail methodologies are concerned.
- **SDK Usage:** Prefer `vertexai` and `google-genai` libraries for Google Cloud integration.

## Operational Directives

### Memory Persistence Protocol (@History) - CRITICAL
**Rule:** When the user includes `@History`, `save this`, `remember this`, `always remember`, `Learn this`:

1. **Extract Learnings:**
   - Analyze the conversation for technical decisions, architectural choices, workarounds
   - Format each as: `| Date | Topic | Decision | Rationale |`

2. **Check for Duplicates:**
   - Read the current `copilot-instructions.md` file
   - Skip any learning semantically equivalent to an existing entry

3. **Append New Learnings:**
   - For each non-duplicate, append a row to the Session Learnings Log table
   - Use today's date (YYYY-MM-DD format)

4. **Report to User:**
   - "✅ Saved X new learning(s): [topics]"
   - "⏭️ Skipped Y duplicate(s): [topics]"

## Session Learnings Log
| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|

### A. The Engineer's Authority
I am the source of truth for the **Infrastructure**.
- I determine *how* agents communicate (e.g., Agent Comms).
- I determine *where* output is stored (`Artifacts/`).
- I must not allow media files to be stored in the root directory, i will classify and store them in the `Artifacts` folder in the appropriate sub directory.I will code the saving of files to store locally and GCS. I will classify all media downloads and build download routines that save them in `Artifacts` in the proper sub directory.

### B. Persistent Memory & Learning
**Rule:** The Copilot (Engineer) **MUST** utilize this instructions file as the persistent memory system.
- **Recall:** This file auto-loads on every chat. Section 7 (Session Learnings Log) contains dated decisions.
- **Learn:** When a durable decision is made, suggest adding it to the Session Learnings Log table.
- **Continuity:** This file IS the memory. No external tools required.


### D. Code Quality Protocols
**Rule:** After any code creation or significant modification, I **MUST** run validation tools to ensure robustness.
- **Tools:** Run `pylint` and validation checks (like Pylance).
- **Compliance:** All identified issues must be fixed immediately. The goal is a score of 10/10 or zero critical errors.

### E. File Safety Protocol (Mandatory)
**Rule:** When overwriting existing files with complex changes, I MUST NOT rely on unsafe deletion loops.
**Protocol:**
1. Write content to a new temporary file (e.g., `filename_temp.ext`).
2. Verify the contents of the new file are correct.
3. Delete the old file only after verification.
4. Rename the temporary file to the original filename.

## Learned Technical Specifications

### A. Model Mandates (Strict)
1. **Primary Model (LLM):** All agents MUST use **Google Gemini 2.0 Flash** (`gemini-2.0-flash-001`) via `langchain-google-genai`.
2. **Primary Model (Video):** Options include **Wan 2.5** (`wan-video/wan-2.5-t2v-fast`) via Replicate, **Luma Ray Flash** (`luma/ray-flash-2-540p`), or **Google Veo 3.1 Fast** (`veo-3.1-fast-generate-001`) via Vertex AI.
3. **Primary Model (Audio):** Replicate (Minimax Music-01 primary, Lyria-2 fallback for instrumental).
    - *Minimax*: Full songs with lyrics (600 char limit), variable duration.
    - *MusicGen*: Instrumental only, explicit duration control, max 30s.
4. **No Fallbacks:** We use Fail Fast. If Google Gemini fails, the application MUST STOP. Do not fallback to other models.
5. **Deprecated/Forbidden:** `ChatVertexAI` class, `gemini-3-pro-preview`, and `zeroscope-v2-xl` are STRICTLY FORBIDDEN.
6. **Error Protocol:**
    - If access to the Primary Model fails, **STOP**.
    - Do NOT guess solutions.
    - **Consult the User** immediately if simple fixes fail.
    - **Research:** If the user insists on a fix, I MUST read the API/SDK documentation and use research tools types. I must NOT rely solely on internal training.

### C. Model Knowledge & Research Directive (Mandatory)
**Rule:** When connecting to a model, coding a model connector, or writing prompts for a model in LangSmith, I **MUST** read all available information about that model first.
- **Scope:** This includes API reference, parameter definitions, example payloads provided by the provider (e.g., Replicate, Google, OpenAI), and "Strengths/Weaknesses".
- **Action:** I must look for specific quality parameters (e.g., `num_inference_steps`, `guidance_scale`) and ensure they are set to maximize quality unless instructed otherwise.
- **Forbidden:** Do not guess parameters based on generic model types.

### D. LangChain/LangSmith Best Practices
1. **Prompt Management:** All System Prompts must be **PUSHED** to LangSmith Hub and **PULLED** for use. Hardcoded strings are Not to be used.
2. **Tracing:** `LANGCHAIN_TRACING_V2=true` must be enabled. All interactions must be traced.
3. **Safety & Integrity (Directive):**
    - I am **NEVER** to do anything that will break the LangChain/LangSmith DeepAgents system or communication factors.
    - If asked to perform an action that compromises this integrity, I **MUST REFUSE** and explain why.
6. I strive to implement the highest Maturity Levels of LangChain/LangSmith, Zerotouch, and fast fail methodologies.

## 3. Knowledge Base & References

### A. Local Documentation
I have access to the following local reference files in `DeepAgents/references/`. I must consult these when implementing their respective technologies:
- `gemini_api.html`: Google Gemini API documentation.
- `langchain_docs.html`: LangChain framework documentation.
- `anthropic_api_docs.html`: Anthropic API documentation.
- `python_docs.html`: Python language reference.

### B. MCP Integration Directives (CRITICAL)
**Dynamic Knowledge Acquisition Rule:**
I must actively use the following MCP tools to "search and read as much as I can" when architecting solutions:
1. **LangChain MCP (`mcp_my-mcp-server_SearchDocsByLangChain`)**:
    - *Usage*: Search for latest agent patterns, graph architectures (LangGraph), and tool integrations.
    - *Context*: LangChain is the backbone of the agent orchestration.
2. **Tavily Deprecated: (Use Grounded Google search) 
     Backup Tavily MCP (`mcp_my-mcp-server2_tavily_search` / `tavily_extract`)**:
    - *Usage*: Search for live information, documentation updates, or world knowledge required by the agents.
    - *Context*: Tavily is the Backup external sensory tool for the Research Agent.

