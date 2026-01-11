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

**Status**: Ready for Ignition.
