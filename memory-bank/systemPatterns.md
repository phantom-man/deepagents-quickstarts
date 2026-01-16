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

### 6a. Command-Based Mesh Routing (LangGraph Gold Standard)

- **Pattern**: All agent nodes in the StateGraph return `Command[Literal[...]]` instead of plain state dictionaries.
- **HANDOFF Protocol**: Delegation tools return `HANDOFF:agent_name:directive` strings. The node function parses these from `ToolMessage` content and routes accordingly.
- **Implementation**:
  ```python
  from langgraph.types import Command
  from typing import Literal
  
  def agent_node(state) -> Command[Literal["other_agent", "__end__"]]:
      # ... invoke agent ...
      handoff = _parse_handoff(response)  # e.g., "HANDOFF:composer:generate music"
      if handoff:
          return Command(update={...}, goto=handoff[0])
      return Command(update={...}, goto="__end__")
  ```
- **No Conditional Edges**: Graph assembly uses ONLY `add_node()` and `set_entry_point()`. All routing decisions are made dynamically by Command returns.
- **Agent Tool Sets**: Each agent receives a curated set of delegation tools (`DIRECTOR_TOOLS`, `COMPOSER_TOOLS`, etc.) from `inter_agent_comms.py`.
- **Rationale**: This is the highest-maturity LangGraph pattern for multi-agent orchestration. It eliminates brittle hardcoded routing and enables true emergent agent collaboration.

### 7. Human-in-the-Loop (HITL) Gate

- **Blocking Signal**: Agents generating expensive/creative assets (Image/Music) yield a specific string `HITL_REVIEW_REQUIRED: {id}`.
- **Persistence**: A simple JSON store (`approval_manager.py`) tracks approved IDs.
- **Resume**: The Agent is re-invoked. It checks the DB. If approved, it returns the asset path. If rejected, it triggers a retry loop.

### 8. Cloud-Primary Asset Identification

- **Identity**: Assets are identified by their **Cloud URL** (GCS) whenever possible, rather than local paths.
- **Rationale**: Local paths break in distributed traces (LangSmith). Cloud URLs are universally resolvable.

### 9. Configuration-Driven Interface (The Matrix)

- **Source of Truth**: LangSmith Hub (`deepagents-system-config`) is the single source of truth for:
  - **Agent Models**: Which LLM to use.
  - **Capabilities**: Which tools (Video/Audio) are enabled.
  - **Provider Strategies**: How to connect (native SDK vs Middleware).
- **Zero-Touch Logic**: Agents query the Matrix to determine implementation details (e.g., "Use `langchain_google_genai` for Gemini").
- **Priorities**: Agents overload capabilities based on priorities defined in the Matrix.

### 10. Zero-Touch Prompt Management (Hub-First)

- **Pattern**: "Self-Healing Hub Integration".
- **Problem**: Hardcoded prompts in Python files drift from remote versions and are hard to edit.
- **Solution**:
  - `prompts.py` files act as the interface layer.
  - Logic: Try `CLIENT.pull_prompt(repo)`.
  - Fallback: If 404/Missing, `CLIENT.push_prompt(repo, local_default)`.
- **Benfit**: The code always works (default fallback), but the "Truth" lives in the Hub, editable by non-coders.

### 5. Negative Feedback Loop

The system learns from failure via explicit rejection logs:

- `bad_examples.md` stores failed outputs (e.g., hallucinated research).
- Agents MUST read this file during initialization to avoid repeating mistakes.

### 14. Phase-Based Prompting (Meta-Cognitive Polymer)
- **Problem**: Agents hallucinate content (e.g., Lyrics in Instrumental tracks) when "Generating" and "Thinking" occur in the same pass.
- **Solution**: Break prompts into **PHASE 1 (Audit/Classify)** and **PHASE 2 (Execute)**.
- **Pattern**: The Agent must first output a classification (e.g., "Mode: Instrumental") which activates negative constraints for the subsequent generation block.

### 15. Native Search Grounding (Google)
- **Deprecation**: `Tavily` is deprecated for Google-based agents.
- **New Standard**: Use `google_search` tool natively embedded in `ChatGoogleGenerativeAI`.
- **Reasoning**: Lower latency, better citation integration, and unified billing/quota with the Vertex AI stack.

### 16. Terminal Output Safety (Pipe-to-File)

- **Problem**: Large text output freezes the terminal (buffer scroll-lock), requiring manual `Enter` key presses to proceed.
- **Protocol**: When querying large datasets, logs, or search results, **ALWAYS** pipe the output to a temporary file (e.g., `temp_output.txt`) and then read the file. **NEVER** print massive strings directly to `stdout`.

### 13. Deprecation Policy (Latest & Greatest)

- **Rule**: Usage of deprecated code is strictly **FORBIDDEN**.
- **Enforcement**:
  - **SDKs**: Use `langchain-google-genai` (modern) instead of `langchain-google-vertexai` (legacy).
  - **Models**: Always use the latest stable model release (e.g., `gemini-2.0-flash-001`).
  - **Audit**: Regularly scan for warnings and refactor immediately.

### 11. Director Agent (Strict Planner Pattern)

- **Role**: Pure generation of textual plans (Creative Directives).
- **Constraints**:
  - **No Tools**: The Director MUST NOT have access to tools (`validate_scene_logic`, `assemble_final_cut`). This prevents `GraphRecursionError` caused by infinite validation loops or hallucinated tool calls.
  - **Prompt Engineering**: The prompt must explicitly forbid "reviewing" or "summarizing" the plan. It must output the plan directly.

## Design Patterns

### Zero-Touch Initialization (GUI)

- **Pattern**: Diagnostic checks run immediately upon module import or app startup.
- **Gating**: The UI is strictly enabled/disabled based on health checks (`failed_systems` list).
- **Visuals**: "Traffic Light" dashboard (Green/Red) replaces manual "Check" buttons.
- **Retry**: Re-initialization is only offered if a failure is detected.

### The "Jewel Standard" (Code Quality)

- **Rule**: Code must be linted and type-checked immediately after creation.
- **Philosophy**: "Mediocrity is a bug."

### The "Cardinal Context" Rule (Workflow)

- **Rule**: When opening any code file for editing, I MUST read the entire file first to gain full context before applying changes.
- **Why**: Blind edits based on assumptions or partial reads lead to regression, import errors, and logic disconnects.
- **Protocol**: `read_file(path, 1, 1000)` -> Analyze -> Plan -> Edit.

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
