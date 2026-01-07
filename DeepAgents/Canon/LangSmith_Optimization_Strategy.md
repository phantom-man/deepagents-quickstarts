# LangSmith Optimization & Tracing Strategy

## Purpose
To enable granular evaluation of agent efficiency, cost, and accuracy, all agent executions must be traced with standardized metadata and tags in LangSmith.

## Tagging Schema
Tags are high-level filtering labels.

- **System Tags**:
  - `deep-agents-system`: All runs from this application.
  - `gui-triggered`: Runs initiated via the Streamlit GUI.
  - `cli-triggered`: Runs initiated via command line (if applicable).

- **Agent Tags**:
  - `agent:director`: Runs involving the Director Agent.
  - `agent:researcher`: Runs involving the Research Agent.
  - `agent:confidence`: Runs involving the Confidence/Verification Agent.

- **Workflow Tags**:
  - `workflow:planning`: Phase where the agent is breaking down tasks.
  - `workflow:execution`: Phase where tools are being called.
  - `workflow:verification`: Phase where the "Trust-But-Verify" logic is active.

## Metadata Schema
Metadata provides specific key-value context for querying and regression testing.

| Key | Description | Example |
| :--- | :--- | :--- |
| `session_id` | Unique ID for the GUI or user session | `session_26f1a...` |
| `agent_mode` | The specific configuration mode | `trust-but-verify`, `fast-research` |
| `model_name` | The underlying LLM used | `gemini-2.0-flash-exp` |
| `parent_run_id` | ID of the orchestrating run (if sub-agent) | `run_abc123...` |
| `user_intent` | Category of user request (optional) | `research_request`, `creative_writing` |

## Evaluation Strategy
To evaluate efficiency:
1. **Filter by `session_id`** to see the full trace of a user interaction.
2. **Group by `model_name`** to compare latency and token usage between Gemini and other models.
3. **Inspect `workflow:verification`** tags to audit the "Trust-But-Verify" loops specifically.
