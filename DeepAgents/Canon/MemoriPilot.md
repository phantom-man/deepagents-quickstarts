# MemoriPilot Session Log

## Session: January 11, 2026 - Google Stack Migration & Stabilization

### 1. System Overhaul

- **Objective**: Migrate from Replicate-centric to Google Vertex AI-centric architecture for cost/performance optimization while retaining Replicate as a fallback.
- **Challenge**: Initial attempts to use `gemini-3-pro-preview` and `lyria` failed due to severe quota restrictions (2 RPM).
- **Solution**: "Winning Stack" identified via `probe_quotas.py`.
  - **Brain**: `gemini-2.0-flash-001` (Fast, High Quota).
  - **Vision**: `imagen-4.0-fast-generate-001` (Fast).
  - **Video/Audio**: Retained Replicate (`zeroscope`, `xtts-v2`) due to Google blocks.

### 2. Architectural Integirty (LangChain/LangSmith)

- **Problem**: `deepagents` middleware library (v0.3.1) caused Pydantic validation errors (`1 validation error...`) when wrapping modern `ChatGoogleGenerativeAI` objects.
- **Fix**: Disabled middleware in `DeepAgents/agent_factory.py`. Reverted to native `langgraph.prebuilt.create_react_agent`.
- **Refinement**: Swapped legacy `ChatVertexAI` (foundational) for `ChatGoogleGenerativeAI` (modern) in all agent definitions to enable native tool binding.
- **Observability**: valid `LANGCHAIN_TRACING_V2=true` confirmed in `studio.py`.

### 3. Code Modifications

- `DeepAgents/studio.py`: Now loads configuration from `data/agent_config.json`.
- `DeepAgents/CommercialAgents/director_agent/agent.py`: Updated to use `ChatGoogleGenerativeAI` and `gemini-2.0-flash-001`.
- `DeepAgents/CommercialAgents/cinematographer_agent/agent.py`: Added distinct `Google` execution path for Image Generation alongside Replicate fallback.
- `DeepAgents/CommercialAgents/research_agent/agent.py`: Updated default model to `gemini-2.0-flash-001`.

### 4. Configuration

- `data/agent_config.json` fully updated to reflect the hybrid Google/Replicate stack.

### 5. LangSmith Authentication Fix (Jan 11, 2026)

- **Problem**: `HTTP 400 No Owner`/`403 Forbidden` errors when pulling prompts from LangSmith Hub, despite valid keys in `.env`.
- **Root Cause**: Organization-Scoped Keys require an explicit `workspace_id` context. The previous implementation relied on `os.environ`, which was unreliable in the complex `ignite_atlas` runtime (likely due to import ordering or caching).
- **Resolution**: Refactored `DeepAgents/hub_manager.py` to:
  1. Dynamically load `.env`.
  2. Extract `LANGSMITH_WORKSPACE_ID`.
  3. Inject it directly into the `Client(api_key=..., workspace_id=...)` constructor.
- **Outcome**: Prompt sync restored. "Strict Mode" (crash on missing prompt) is now safe to enable.

**Status**: Ready for Ignition.

### 6. Anthropic & Observability Shift (January 12, 2026)

- **Change Directive**: User mandated immediate switch from Google Gemini to **Anthropic Claude 3 Haiku** as the primary cognitive engine.
- **Reasoning**: Stability and Ontology alignment ("Cognitive Engine" definition).
- **Observability**: Removed `OTLP` (OpenTelemetry) local collector requirement. Switched to direct **LangChain Tracing** (Cloud).
- **Instruction Sync**: `copilot-instructions.md` updated to reflect absolute paths (`../DeepAgents/...`) and the new tech stack to prevent hallucination of legacy configs.
- **Outcome**: System Instructions now align with the `system_config.py` reality.

### 7. Zero Touch & Fail Fast (January 15, 2026)

- **Directive**: STRICT Zero Touch enforcement. No hardcoded configuration overrides in Agent factories. All configuration MUST derive from LangSmith Hub via `SystemConfiguration`.
- **Methodology**: "Fail Fast".
  - REMOVED all fallback logic (e.g., `try-except` blocks that switched to Haiku/Replicate on failure).
  - REMOVED local default dictionaries in `SystemConfiguration` if Hub pull fails (It must now Raise Error).
  - UPDATED Co-pilot instructions to explicitly forbid fallback patterns.
- **State**: The system is now brittle by design—it works correctly (Google Gemini) or it crashes visibly. This exposes errors immediately rather than concealing them.

**Status**: Instructions Synced. Codebase Logic Aligned.

### 8. Command-Based Mesh Routing Architecture (January 16, 2026)

- **Problem**: Director Agent was generating plans but NOT delegating to production agents (Composer, Cinematographer, Editor). Routing was hardcoded via conditional edges in the StateGraph.
- **Root Cause**: Agents lacked inter-agent communication tools and graph edges were statically defined rather than dynamically determined by agent decisions.
- **Solution**: Implemented LangGraph's **Command Pattern** for dynamic multi-agent routing.
  - **HANDOFF Protocol**: Agents return `HANDOFF:agent_name:directive` strings via delegation tools.
  - **Command Return**: Each node parses tool responses for HANDOFF patterns and returns `Command[Literal["director", "researcher", "validator", "cinematographer", "composer", "editor", "__end__"]]`.
  - **No Explicit Edges**: Graph assembly uses ONLY `add_node()` and `set_entry_point()`. Routing is entirely determined by Command returns.
- **Tools Created**: 
  - `discover_agents()` - Lists all available agents and capabilities
  - `delegate_to_director/researcher/confidence/composer/cinematographer/editor()` - Returns HANDOFF strings
  - `signal_task_complete()` - Returns END signal
  - Agent-specific tool sets: `DIRECTOR_TOOLS`, `RESEARCHER_TOOLS`, `CONFIDENCE_TOOLS`, `COMPOSER_TOOLS`, `CINEMATOGRAPHER_TOOLS`, `EDITOR_TOOLS`
- **Files Modified**:
  - `DeepAgents/inter_agent_comms.py` - Central delegation tool hub
  - `DeepAgents/graphs/agency_graph.py` - All 6 nodes now return Command
  - `DeepAgents/CommercialAgents/director_agent/agent.py` - Uses DIRECTOR_TOOLS
- **Architectural Significance**: This is the "highest maturity" LangGraph pattern. Agents now form a true **mesh network** where any agent can discover and delegate to any other agent at runtime.

**Status**: Full Mesh Architecture Deployed. Server Live.

### 7. LangGraph Server Protocol Optimization (January 13, 2026)

- **Problem**: Repeated failures when starting `langgraph_cli` from Project Root (`Invalid value for '--config'`).
- **Diagnosis**: `langgraph.json` contains relative paths (`./graph_app.py`) that fail unless the shell's active directory is `DeepAgents/`.
- **Learning**: The server MUST be launched from the subdirectory context.
- **Action**: Updated `copilot-instructions.md` with the compulsory command pattern: `cd DeepAgents; python -m langgraph_cli dev ...`.
- **Outcome**: Zero-shot server startup reliability established.

**Status**: Operational Protocols Hardened.
