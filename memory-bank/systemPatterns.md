# System Patterns

## Architecture & Tech Stack

The core architecture of "Atlas" (DeepAgents) relies on a hybrid persistence model and an ontology-driven agent design.

### Core Technologies

- **LLM**: Google Gemini (Pro/Flash) via `google-genai` SDK.
- **Vector Database**: LanceDB (768 dimensions via `text-embedding-004`).
- **Nervous System (OLTP)**: PostgreSQL via `psycopg` (Async V3) and `psycopg2` (Sync Legacy).
- **Orchestration**: LangGraph with `langgraph-checkpoint-postgres`.
- **Observability (OTLP)**: OpenTelemetry via LangSmith (`LANGSMITH_OTEL_ENABLED=true`).
- **Voice**: XTTS-v2 via Replicate.
- **GUI**: Streamlit with Asyncio Bridge.

## Architectural Patterns

### 1. The Nervous System (Hybrid Persistence)

The system maintains two distinct types of "Memory":

- **Hippocampus (Semantic)**: LanceDB stores unstructured vectors (documents, learnings).
- **Nervous System (Reflex/State)**: PostgreSQL stores:
  - **Sync State**: Tool configurations, global registry (`agent_brain.py` via `psycopg2`).
  - **Async State**: LangGraph checkpoints for pausing/resuming agent threads (`persistence.py` via `psycopg` V3).

### 2. Async-Sync Bridge (UI Layer)

Streamlit runs synchronously. To support the modern Async LangGraph architecture, the GUI utilizes an `asyncio.run()` bridge pattern:

- The UI initializes a dedicated Event Loop (using `WindowsSelectorEventLoopPolicy` on Windows).
- It invokes async agent runners which yield events back to the sync UI stream.

### 3. Ontology-Driven Agents

Agents are not just prompts; they are defined by rigid **Ontologies** (Markdown/JSON) that dictate their:

- **Identity**: "Who am I?"
- **Epistemic Rules**: "How do I verify truth?"
- **Output Standards**: "What format is required?"
Rules:
- Ontologies are ingested at runtime via MemoriPilot.
- Ontologies are "Constitution-grade" (immutable during execution).

### 5. Deployment Constraints (Windows/Dev vs Prod)

- **Windows Development**: The `langgraph_cli` server on Windows encounters `BlockingIOError` (WinError 183) during file operations (shutil.move).
  - **Workaround**: ALL local dev servers on Windows must run with `--allow-blocking`.
  - **Trade-off**: This couples the event loop, potentially slowing down concurrent requests.
- **Production**:
  - MUST set `BG_JOB_ISOLATED_LOOPS=true` to ensure background workers do not block the main API loop.
  - Code should be migrated to pure `asyncio` patterns where possible to remove the need for blocking permission.

### 6. Meta-Discovery System
- **Discovery**: Agents possess a `discover_agents` tool. If they encounter a task outside their domain, they query the registry to find a peer who can handle it.
- **Dynamic Handoff**: This allows for emergent behavior (e.g., Cinematographer realizing they need music and calling Composer directly).

### 5. Negative Feedback Loop

The system learns from failure via explicit rejection logs:

- `bad_examples.md` stores failed outputs (e.g., hallucinated research).
- Agents MUST read this file during initialization to avoid repeating mistakes.

## Design Patterns

### Zero-Touch Initialization (GUI)

- **Pattern**: Diagnostic checks run immediately upon module import or app startup.
- **Gating**: The UI is strictly enabled/disabled based on health checks (`failed_systems` list).
- **Visuals**: "Traffic Light" dashboard (Green/Red) replaces manual "Check" buttons.
- **Retry**: Re-initialization is only offered if a failure is detected.

### The "Jewel Standard" (Code Quality)

- **Rule**: Code must be linted and type-checked immediately after creation.
- **Philosophy**: "Mediocrity is a bug."

## Common Idioms

- **Tool Call Injection**: `consult_research_agent` is injected as a tool capability into the Director, allowing dynamic delegation.
- **MemoriPilot**: The Copilot (Developer) maintains a persistent "active context" file to track session continuity.

## Modern Google/LangGraph Integration Pattern

When integrating Google Gemini models (especially 2.0 Flash) with LangGraph: 1) Use `ChatGoogleGenerativeAI` from `langchain_google_genai`, NOT `ChatVertexAI`. 2) Use native `.bind_tools()` on the model object. 3) Avoid custom wrapper middleware like `deepagents` v0.3.1 which may suffer from schema misalignment with new Google objects. 4) Always define a clear fallback path (e.g. to Replicate) for robust production flows.

## Strict Connectivity & Hybrid Async Bridge

Core patterns governing the agent architecture, failure modes, and synchronization.

### Examples

- Hub Manager: Raises error if Hub unreachable (No Failover).
- GUI Bridge: Uses asyncio.WindowsSelectorEventLoopPolicy for async UI.
- Smart Defaults: GUI defaults to provider strengths (Anthropic/Replicate).

### LangSmith Organization Key Injection

When using LangSmith Organization-Scoped API Keys (starting with `lsv2_pt_...`), standard environment variable auto-discovery (`LANGCHAIN_PROJECT_ID`) is insufficient in complex runtimes.

- **Pattern**: Manually parse the `.env` file to retrieve `LANGSMITH_WORKSPACE_ID`.
- **Implementation**: Explicitly pass `workspace_id` to the `Client` constructor.

  ```python
  client = Client(
      api_key=os.getenv("LANGCHAIN_API_KEY"),
      workspace_id=os.getenv("LANGSMITH_WORKSPACE_ID")  # CRITICAL for Org Keys
  )
  ```

- **Reasoning**: This bypasses `os.environ` ambiguity and ensures prompts are pulled from the correct organization scope.
