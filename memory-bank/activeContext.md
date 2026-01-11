# Active Context

## Current Goals

- Refactored `agent_factory.py` to use `langgraph.prebuilt.create_react_agent`, aligning with best practices.
- Preserved legacy logic in `agent_factory_legacy.py`.
- Verified Director Agent creation with Anthropic Haiku.
- System state matches best practices for standard LLMs (Anthropic/Google).
- Next: Proceed with system ignition or further requests.

## Recent Changes

- **Infrastructure Migration**: Shifted primary intelligence and vision to Google Vertex AI (`Gemini 2.0 Flash`, `Imagen 4 Fast`) to optimize for speed/quota.
- **Middleware Adjustment**: Disabled `deepagents-v0.3.1` middleware in `agent_factory.py` to resolve Pydantic validation crashes; reverted to native `LangGraph`.
- **Implementation Update**: Replaced legacy `ChatVertexAI` with modern `ChatGoogleGenerativeAI` across all major agents (`Director`, `Cinematographer`, `Researcher`).
- **Optimization**: Verified "Winning Stack" quotas via `probe_quotas.py`, identifying safe high-throughput models.
- **Observability (OTLP)**: Installed `langsmith[otel]` and configured `agent_runner.py` to emit OpenTelemetry traces.
- **Persistence (OLTP)**: Updated `agent_runner.py` to use `DeepAgents/persistence.py` (AsyncPostgresSaver) for robust state management.

## Active Questions

- Does the new Google-based Director Agent correctly bind tools and execute the full commercial pipeline?
- Does the Replicate fallback logic in `Cinematographer` successfully catch any Google Imagen errors?
- Are traces appearing correctly in LangSmith?

## Next Steps

1. **Ignite Atlas**: Run `python DeepAgents/ignite_atlas.py` to start the production studio.
2. **Verify Director**: Issue a complex task to test the new Gemini 2.0 Flash brain.
3. **Verify Cinematographer**: Request a storyboard to test Imagen 4 Fast integration.
4. **Monitor**: Check LangSmith for clean traces and cost tracking.
