## Active Context

### Current Focus

- **Component**: Operations & Deployment
- **Task**: Finalize Human-in-the-Loop implementation and consolidate project state.
- **Recent Success**:
  - **HITL Verification**: Confirmed effective "Pause/Resume" logic in Agent Runners.
  - **Cloud Compatibility**: Prioritized GCS URLs in approval signals to ensure LangSmith usage.
  - **Dependency Lock**: Updated `requirements.txt` to match the exact Development Environment.

## Recent Changes

- **Human-in-the-Loop (2026-01-14)**:
  - **Architecture**: Implemented blocking "Approval Gate" in `DeepAgents/approval_manager.py`.
  - **LangSmith Fix**: Modified Agents to yield `https://` URLs for approval requests instead of `C:\` paths, enabling remote management.
  - **GUI Integration**: Added "Approve/Reject" controls to the Streamlit interface that intercept these signals.
- **Logic Hardening (2026-01-14)**:
  - **Confidence Agent**: Updated prompt to act as "The Editor" with a precise JSON scoring contract. Passing score is > 0.8.
  - **Researcher Agent**: Added mandatory `submit_finding_for_review` tool. Automatically logs failures to LanceDB ("Negative Reinforcement") and successes to Memory ("Positive Reinforcement").
  - **Copilot Instructions**: Added mandate to "Evaluate need for research" as the FIRST action after receiving a prompt.
- **Ontology Consolidation (2026-01-14)**:
  - **Action**: Deprecated `Director_Ontology.md`, `Cinematographer_Ontology.md`, and `Composer_Ontology.md`. They now point to `MASTER_ONTOLOGY.md`.
  - **Logic**: All prompt engineering is now "Zero Touch" and lives in LangSmith Hub (`*-system-prompt` repos).
  - **Prompt Updates**: Updated Python `DEFAULT_` strings to forbid Google Veo and mandate full prompt reading, ensuring even fallbacks are compliant.
- **Legacy Artifact Migration (2026-01-14)**:
  - **Backfill**: Implemented `migrate_artifacts.py` to scan local `Artifacts/` and upload legacy files to Google Cloud Storage.
  - **Sync Logic**: Added `sync_local_to_cloud()` to `AssetManager` to ensure metadata consistency (injecting `cloud_url`).
  - **Git Hygiene**: Updated `.gitignore` to exclude heavy media binary blobs while preserving lightweight JSON metadata.
- **Zero Touch GUI AUDIT (2026-01-14)**:
  - **Refactor**: Cleaned `DeepAgents/gui/app.py` to remove all legacy hardcoded model selectors.
  - **Lockdown**: Interface is now fully driven by `SystemConfiguration` loaded from LangSmith.
- **Provider Strategy Centralization (2026-01-14)**:
  - **Action**: Moved the definition of *how* to connect to providers (e.g., "Use `ChatGoogleGenerativeAI`") into the LangSmith Hub configuration.
  - **Benefit**: Changing underlying SDKs or implementation classes can now be signaled via configuration, effectively decoupling logic from hardcoded choices.
- **Asset Storage & GCS (2026-01-14)**:
  - **GCS Integration**: `AssetManager` calls implicit GCP Auth to upload every generated asset to a public-read path.
  - **Cinematographer Update**: Refactored `_generate_image/video` tools to fetch and return this Cloud URL.
  - **Config Matrix**: Updated `Cinematographer` capabilities in the System Configuration to include `image_generation` (Google Imagen 3 / Flux).
- **Configuration Refactor (2026-01-13)**:
  - **Dynamic System**: Removed hardcoded GUI model selectors. Implemented `SystemConfiguration` to hydrate agent capabilities from LangSmith Hub (`deepagents-system-config`).
  - **Asset Consolidation**: Moved all data/assets to `Artifacts/`. Updated `AssetManager` to use global paths defined in the system config.
  - **Overloaded Capabilities**: Composer Agent now selects its music engine dynamically based on highest priority in the config matrix.
- **Audio Quality Decision (2026-01-13)**:
  - **Decision**: ACE-Step quality was inconsistent. Minimax 1.5 is "Radio Quality" but has strict limits.
  - **Strategy**: Instead of fighting the limit, we optimized the prompt to "maximize density" (Short lines, compressed imagery) to fit a full song into 600 chars.
- **Music Generation Upgrade (2026-01-13)**:
  - **Default Model**: Switched from ACE-Step back to `minimax/music-1.5`.
  - **Smart Prompting**: Composer now intelligently auto-generates rich technical tags or expands user styles (e.g. "Beatles") into detailed production descriptors.
  - **Parameter Tuning**: Hardcoded optimal `euler` scheduler and `apg` guidance settings based on model documentation.
- **Reliability Engineering**:
  - **Replicate URL Normalization**: Implemented `_extract_replicate_url` in Composer Agent to handle inconsistent return types (Lists vs Strings) from Minimax/MusicGen.
  - **Static Analysis**: Conducted a comprehensive Pylance sweep, fixing type hint errors (e.g., `ChatAnthropic` signature mismatches) and suppressing noisy OpenTelemetry (`opentelemetry.attributes`) logs.
- **Meta-Discovery System**:
  - **Concept**: Agents are no longer isolated silos. They can query the `AgencyRegistry` to find peers based on skills.
  - **Implementation**: Added `discover_agents` tool to Director and Cinematographer.
- **Mesh Topology Implementation**:
  - **Cinematographer Upgrade**: Completely rewrote `cinematographer_agent/agent.py`. It is no longer a linear script but a dynamic Agent that binds tools (`generate_image`, `generate_video`, `consult_composer`).
  - **Autonomy**: The Cinematographer now decides *order of operations* (e.g., "Get music first to understand the mood").
- **Schema Enforcement (Composer)**:
  - **Dynamic Prompting**: Hardcoded the Minimax Music-1.5 schema (Verse/Chorus/Bridge/Outro) and strict character budgets directly into the `_generate_lyrics_and_style` prompt.
  - **Anti-Hallucination**: Modified `generate_music_tool` return values to include `**(Verified Lyrics Used)**`, effectively forcing the Agent to report reality rather than invention.
- **Identity Shift**: Renamed the Director Agent's identity to **[APOLLO]**. Updated `director-system-prompt` on LangSmith Hub.
- **Hub Hygiene**: Created `cleanup_prompts.py` to remove legacy `*-main` repositories. Updated `push_prompts.py` to strictly use the `*-system-prompt` naming convention.
- **Hub Authentication Fix**: Refactored `DeepAgents/hub_manager.py` to instantiate `langsmith.Client` with dynamic arguments (`api_key`, `workspace_id`) derived from the `.env` file. This bypasses the flaky `os.environ` behavior in the complex application runtime.
- **Composer Upgrade**: Switched the primary music generation engine from `minimax/music-01` to `minimax/music-1.5`.
- **Composer Stability**: Fixed a critical recursion bug where the Composer Agent called its own factory. Implemented `generate_music_tool` for direct, non-recursive API access, ensuring reliable execution.

## Active Questions

- **Optimization**: Can the "Compressed Imagery" prompting strategy consistently fit a full song arc into Minimax's 600-character limit without losing narrative depth?

## Next Steps

1. **Verify Minimax**: Use LangGraph Studio to send a test request using the new dense prompting style.
2. **Monitor**: Listen to the generated audio for "Outro" completion (ensure the song didn't get cut off).
