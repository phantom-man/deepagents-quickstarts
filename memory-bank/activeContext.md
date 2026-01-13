## Active Context

### Current Focus
- **Component**: Cinematographer Agent (Lumiere) & Orchestration.
- **Task**: Implementing "Mesh Topology" where agents can call each other (Cinematographer calls Composer) to simplify orchestration.
- **Recent Success**: 
  - Refactored `Cinematographer Agent` (Generator Pattern) to use a manual ReAct loop, allowing it to "Think" and "Act" using internal tools.
  - Enabled **Inter-Agent Communication**: Cinematographer can now autonomously call `consult_composer` to get music before generating video.
  - Verified with `test_cinema_tools.py`: Cinematographer successfully ordered music (Composer/Minimax) and an image (Google/Imagen) in one session.
- **Next Step**: Configure the Director/Editor to merge these assets into a final video file.

## Recent Changes

- **Mesh Topology Implementation**:
  - **Cinematographer Upgrade**: Completely rewrote `cinematographer_agent/agent.py`. It is no longer a linear script but a dynamic Agent that binds tools (`generate_image`, `generate_video`, `consult_composer`).
  - **Autonomy**: The Cinematographer now decides *order of operations* (e.g., "Get music first to understand the mood").
- **Schema Enforcement (Composer)**:
  - **Dynamic Prompting**: Hardcoded the Minimax Music-1.5 schema (Verse/Chorus/Bridge/Outro) and strict character budgets directly into the `_generate_lyrics_and_style` prompt.

  - **Anti-Hallucination**: Modified `generate_music_tool` return values to include `**(Verified Lyrics Used)**`, effectively forcing the Agent to report reality rather than invention.
- **GUI Restoration**: Fixed `NameError` (undefined `model` variable) in `DeepAgents/gui/app.py`. The Streamlit app now launches successfully and model selection logic is robust.
- **GUI Restoration**: Fixed multiple `IndentationError` and `SyntaxError` issues in `DeepAgents/gui/app.py`.
- **Composer Fixes**:
  - Corrected `voice_dir` pathing logic in `DeepAgents/CommercialAgents/composer_agent.py` to correctly locate assets in `data/voices`.
  - Added `.mp3` support to voice discovery logic.
  - Fixed Replicate payload schema for `minimax/music-01` (Changed `refer_voice` to `voice_file`).
  - Implemented robust fallback logic: If Minimax fails (E004/E006), the system now seamlessly degrades to `MusicGen` to ensure the user always gets an audio result.
- **Identity Shift**: Renamed the Director Agent's identity to **[APOLLO]**. Updated `director-system-prompt` on LangSmith Hub.
- **Hub Hygiene**: Created `cleanup_prompts.py` to remove legacy `*-main` repositories. Updated `push_prompts.py` to strictly use the `*-system-prompt` naming convention.
- **Hub Authentication Fix**: Refactored `DeepAgents/hub_manager.py` to instantiate `langsmith.Client` with dynamic arguments (`api_key`, `workspace_id`) derived from the `.env` file. This bypasses the flaky `os.environ` behavior in the complex application runtime.
- **Verification**: Confirmed successful prompt pulls (`director-system-prompt`, `researcher-system-prompt`) via the fixed manager.
- **Infrastructure Migration**: Shifted primary intelligence and vision to Google Vertex AI (`Gemini 2.0 Flash`, `Imagen 4 Fast`) to optimize for speed/quota.
- **Middleware Adjustment**: Disabled `deepagents-v0.3.1` middleware in `agent_factory.py` to resolve Pydantic validation crashes; reverted to native `LangGraph`.
- **Implementation Update**: Replaced legacy `ChatVertexAI` with modern `ChatGoogleGenerativeAI` across all major agents (`Apollo`, `Cinematographer`, `Researcher`).
- **Optimization**: Verified "Winning Stack" quotas via `probe_quotas.py`, identifying safe high-throughput models.
- **Observability (OTLP)**: Installed `langsmith[otel]` and configured `agent_runner.py` to emit OpenTelemetry traces.
- **Persistence (OLTP)**: Updated `agent_runner.py` to use `DeepAgents/persistence.py` (AsyncPostgresSaver) for robust state management.
- **Dependency Resolution**: Installed `psycopg-binary` and `arxiv` to resolve `ImportError` crashes. Verified `requirements.txt` reflects the migration to `psycopg` (v3) for Async Postgres support.
- **Composer Stability**: Fixed a critical recursion bug where the Composer Agent called its own factory. Implemented `generate_music_tool` for direct, non-recursive API access, ensuring reliable audio generation.
- **Best Practices Implementation**:
  - **Retries**: Implemented `tenacity` with exponential backoff in `run_director_eval.py` to handle API rate limits robustly.
  - **Configuration**: Updated `.env.example` to explicitly include `OTEL_EXPORTER_OTLP_ENDPOINT`, making observability setup transparent.
  - **Linting**: Created `.pylintrc` to suppress noisy `import-error` warnings, improving the developer experience.
- **Composer Upgrade**: Switched the primary music generation engine from `minimax/music-01` to `minimax/music-1.5`.
  - **Reason**: `music-01` required `mp3` inputs for voice/instrumental references, causing failures with Lyria-generated `wav` files in environments lacking `ffmpeg`.
  - **Benefit**: `music-1.5` generates full capability audio from text/lyrics alone, removing the complex two-step pipeline and file format dependency.

## Active Questions

- Does the new `generate_music_tool` correctly handle all Minimax/MusicGen API edge cases in production?
- Does the new Google-based Apollo Agent correctly bind tools and execute the full commercial pipeline?
- Does the Replicate fallback logic in `Cinematographer` successfully catch any Google Imagen errors?
- Are traces appearing correctly in LangSmith?

## Next Steps

1. **Verify Composer**: Confirm generation quality in the GUI.
2. **Verify Apollo**: Issue a complex task via the GUI to test the new Gemini 2.0 Flash brain.
3. **Verify Cinematographer**: Request a storyboard to test Imagen 4 Fast integration.
4. **Monitor**: Check LangSmith for clean traces and cost tracking.
