# Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-11 | Adopted XTTS-v2 (via Replicate) as the primary Voice Engine. | The previously used Minimax API was unavailable/unreliable, and Bark was too slow for real-time interaction. XTTS-v2 offers a good balance of quality and latency, supported by local reference audio injection. |
| 2026-01-11 | Renamed application entry point from DeepAgents.py to orchestrator.py. | The file name 'DeepAgents.py' collided with the installed middleware package 'deepagents', causing circular import errors and namespace confusion. |
| 2026-01-11 | Standardized on OpenTelemetry (OTLP) for Observability. | To ensure consistent tracing across LangSmith and other tools, we enabled OTLP (LANGSMITH_OTEL_ENABLED=true) targeting localhost:4318, providing a vendor-neutral observability path. |
| 2026-01-11 | Enforced MemoriPilot Protocol for Copilot Context. | To solve the issue of Copilot losing context between turns/sessions, we established the Memory Bank (MemoriPilot) as the mandatory 'long-term memory' that must be read/updated every session. |
| 2026-01-11 | Implemented Ontology-Driven Architecture (2026-01-05). | To ensure consistent agent behavior, we moved from pure prompt engineering to JSON-based Ontologies that define concepts and scoring rules. This allows programmatically checking agent outputs against a 'truth' definition. |
| 2026-01-11 | Established Reinforcement Feedback Loop (2026-01-05). | Commercial Agents now use a `bad_examples.md` file. The Confidence Agent rejects poor outputs (Score < 7) and appends them to this file, which is then fed back into the Research Agent's context to prevent repeat mistakes. |
| 2026-01-11 | Standardized Code Quality via Strict Pylinting (2026-01-08). | To ensure maintainability, we enforced a strict 10/10 Pylint standard across all core modules (`agent_brain`, `Copilot`, `model_registry`). |
| 2026-01-11 | Merged Copilot_Ontology.md into .github/copilot-instructions.md. | To consolidate the system's 'Constitution', we merged the Ontology Canon into the primary instructions file. This ensures that every session initialization loads both the MemoriPilot protocol and the architectural/behavioral ontology. |
